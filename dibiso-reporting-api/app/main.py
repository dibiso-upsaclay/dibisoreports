import subprocess
import tempfile
import shutil
import zipfile
import os
import sys
from pathlib import Path
import logging
import uuid
import asyncio
import threading
import time
import concurrent.futures
import urllib.parse
import requests

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Optional, Dict, Annotated
# from starlette.requests import Request
from starlette.responses import JSONResponse

# Not needed as used in a subprocess script
# from dibisoreporting import Biso

load_dotenv()  # Load environment variables from .env file (only for development; when in docker, there is no env file
# to load)

scanr_api_password = os.getenv("SCANR_API_PASSWORD")
scanr_api_url = os.getenv("SCANR_API_URL")
scanr_api_username = os.getenv("SCANR_API_USERNAME")
scanr_bso_index = os.getenv("SCANR_BSO_INDEX")
scanr_publications_index = os.getenv("SCANR_PUBLICATIONS_INDEX")
projects_persistence_time_hours = int(os.getenv("PROJECTS_PERSISTENCE_TIME_HOURS"))
analyses_retention_days = int(os.getenv("PROJECTS_ANALYSES_RETENTION_DAYS", "30"))
html_template_url = os.getenv("HTML_TEMPLATE_URL")
html_template_path = os.getenv("HTML_TEMPLATE_PATH")
openalex_analysis_cache_path = os.getenv("OPENALEX_ANALYSIS_CACHE_PATH")
openalex_api_key = os.getenv("OPENALEX_API_KEY")
openalex_email = os.getenv("OPENALEX_EMAIL")
data_fetching_timeout_seconds = int(os.getenv("DATA_FETCHING_TIMEOUT_SECONDS", "1200"))

# Authentication Imports
from fastapi.security import OAuth2PasswordRequestForm
from .auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_admin_user,
    ACCESS_TOKEN_EXPIRE_HOURS,
    verify_password,
    Token
)

# User Management Imports
from .users import (
    UserCreate,
    UserResponse,
    UserUpdate,
    ProfileUpdate,
    PasswordChange,
    AdminPasswordChange,
    create_user_in_db,
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    update_user_info,
    update_user_info_by_id,
    update_user_profile,
    update_user_password,
    update_user_password_by_id,
    deactivate_user,
    deactivate_user_by_id,
    activate_user_by_id,
    get_all_users,
    init_database,
    is_admin,
    delete_user_by_id,
    get_analyses,
    upsert_analysis,
    delete_analyses,
    delete_old_analyses,
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if openalex_analysis_cache_path is not None:
    if not Path(openalex_analysis_cache_path).exists():
        logger.info(f"Creating OpenAlex analysis cache path: {openalex_analysis_cache_path}")
        Path(openalex_analysis_cache_path).mkdir(parents=True, exist_ok=True)
    logger.info(f"Using OpenAlex analysis cache path: {openalex_analysis_cache_path}")
else:
    logger.warning(f"OpenAlex analysis cache path not found: {openalex_analysis_cache_path}")
    logger.warning(f"OpenAlex analysis will use the default cache path: ~/openalex-analysis/data")

# Request model for report generation
class ReportRequest(BaseModel):
    year: int = Field(..., ge=1000, le=3000, description="Year for the report")
    entity_acronym: str = Field(..., min_length=1, description="Laboratory acronym")
    entity_full_name: str = Field(..., min_length=1, description="Full laboratory name")
    entity_id: str = Field(..., min_length=1, description="HAL collection ID")
    max_entities: int = Field(..., ge=1, le=10000, description="Max entities to use for maps")
    reporter: str = Field("", description="Name of the person writing the report")
    reporter_email: str = Field("", description="Email of the reporter")

thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=int(os.getenv("THREAD_POOL_MAX_WORKERS")))

# Global dictionary to store compilation status
compilation_status: Dict[str, Dict] = {}
compilation_lock = threading.Lock()

data_fetching_processes: Dict[str, subprocess.Popen] = {}
process_lock = threading.Lock()

# Section registry per report type
REPORT_SECTIONS: Dict[str, list] = {
    "biso": [
        {"id": "journals_hal",                  "label": "Liste des revues (HAL)"},
        {"id": "conferences",                   "label": "Liste des conférences"},
        {"id": "chapters",                      "label": "Liste des chapitres"},
        {"id": "works_type",                    "label": "Typologie de la production scientifique"},
        {"id": "open_access_works",             "label": "Articles en accès ouvert"},
        {"id": "journals",                      "label": "Revues et voies d'accès (BSO)"},
        {"id": "collaboration_map_world",       "label": "Carte des collaborations internationales"},
        {"id": "collaboration_map_europe",      "label": "Carte des collaborations européennes"},
        {"id": "collaboration_names",           "label": "Collaborations par établissements"},
        {"id": "private_sector_collaborations", "label": "Collaborations secteur privé"},
        {"id": "european_projects",             "label": "Projets européens"},
        {"id": "anr_projects",                  "label": "Projets ANR"},
        {"id": "data",           "label": "Jeux de données partagés","figure": False},
        {"id": "strengths",      "label": "Atouts du laboratoire",  "figure": False},
        {"id": "recommendations","label": "Préconisations",         "figure": False},
    ],
    "pubpart": [
        {"id": "topics_collaborations",               "label": "Principales thématiques"},
        {"id": "topics_potential_collaborations",     "label": "Potentiel de collaboration"},
        {"id": "institutions_lineage_collaborations", "label": "Top 25 structures internes"},
        {"id": "works_collaborations_normalized",     "label": "Top 25 co-publications (citations normalisées)"},
        {"id": "works_collaborations_count",          "label": "Top 25 co-publications (citations)"},
        {"id": "analysis", "label": "Analyse", "figure": False},
    ],
}


# Cleanup old compilation statuses and files (run periodically)
async def cleanup_old_compilations():
    """
    Clean up compilation statuses older than 1 hour and
    delete temporary directories older than 1 hour based on their modification time.
    """
    while True:
        try:
            await asyncio.sleep(300)  # Check every 5 minutes
            current_time = datetime.now()

            # --- Clean up old compilation statuses in memory ---
            with compilation_lock:
                to_remove_status = []
                for comp_id, status in compilation_status.items():
                    if current_time - status['last_updated'] > timedelta(hours=projects_persistence_time_hours):
                        to_remove_status.append(comp_id)

                for comp_id in to_remove_status:
                    del compilation_status[comp_id]
                    try:
                        delete_analyses(comp_id)
                    except Exception as e:
                        logger.error(f"Error deleting analyses for {comp_id}: {e}")

            if to_remove_status:
                logger.info(f"Cleaned up {len(to_remove_status)} old compilation statuses from memory.")

            # Delete analyses older than analyses_retention_days
            try:
                delete_old_analyses(analyses_retention_days)
            except Exception as e:
                logger.error(f"Error in old analyses cleanup: {e}")

            # --- Clean up old temporary directories on file system ---
            temp_root_dir = Path(tempfile.gettempdir())
            cleaned_up_dirs_count = 0

            # Iterate through all entries in the temporary directory
            for entry in temp_root_dir.iterdir():
                # Check if it's a directory and starts with the expected prefix
                if entry.is_dir() and entry.name.startswith("html_output_"):
                    try:
                        # Get the last modification time of the directory
                        # This serves as a proxy for creation time for these temporary folders.
                        mod_timestamp = entry.stat().st_mtime
                        mod_datetime = datetime.fromtimestamp(mod_timestamp)

                        # If the directory was modified more than an hour ago, delete it
                        if mod_datetime < current_time - timedelta(hours=projects_persistence_time_hours):
                            logger.info(f"Deleting old temporary directory: {entry}")
                            shutil.rmtree(entry)
                            cleaned_up_dirs_count += 1
                    except Exception as e:
                        logger.error(f"Error cleaning up directory {entry}: {e}")

            if cleaned_up_dirs_count > 0:
                logger.info(
                    f"Cleaned up {cleaned_up_dirs_count} old temporary compilation directories from file system."
                )

        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")


async def monitor_thread_pool():
    """Monitor thread pool health and log statistics"""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            active_tasks = len([t for t in asyncio.all_tasks() if not t.done()])
            logger.info(f"Thread pool status - Active tasks: {active_tasks}")

            # Log compilation statuses
            with compilation_lock:
                running_count = len([s for s in compilation_status.values() if s['status'] == 'running'])
                failed_count = len([s for s in compilation_status.values() if s['status'] == 'failed'])
                completed_count = len([s for s in compilation_status.values() if s['status'] == 'completed'])
            logger.info(f"Compilation status - Running: {running_count}, Failed: {failed_count}, Completed: {completed_count}")

        except Exception as e:
            logger.error(f"Error in thread pool monitoring: {e}")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Context manager for managing the lifespan of the FastAPI application.
    """
    logger.info("Application startup: Starting background tasks and initializing database.")
    init_database()

    # Start background tasks
    cleanup_task = asyncio.create_task(cleanup_old_compilations())
    monitor_task = asyncio.create_task(monitor_thread_pool())

    yield

    logger.info("Application shutdown: Performing cleanup.")

    # Cancel background tasks
    cleanup_task.cancel()
    monitor_task.cancel()

    # Shutdown thread pool
    thread_pool.shutdown(wait=True)

    # Cancel any running compilations
    with compilation_lock:
        for comp_id in list(compilation_status.keys()):
            if compilation_status[comp_id]['status'] == 'running':
                compilation_status[comp_id]['status'] = 'cancelled'

    logger.info("Application shutdown complete.")


app = FastAPI(title=os.getenv("API_TITLE"), version=os.getenv("API_VERSION"), lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "").split(","),
    allow_credentials=os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() == "true",
    allow_methods=os.getenv("CORS_ALLOW_METHODS", "").split(","),
    allow_headers=os.getenv("CORS_ALLOW_HEADERS", "").split(","),
)


def not_found_error(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Not Found", "doc_url": urllib.parse.urljoin(str(request.base_url), "docs")},
    )


# Register the error handler using the app.exception_handler decorator
@app.exception_handler(404)
def not_found_exception_handler(request: Request, exc: HTTPException):
    return not_found_error(request, exc)


# Authentication endpoints
@app.post("/admin/register", response_model=UserResponse)
async def admin_register_user(
    user_data: UserCreate,
    current_admin: Annotated[dict, Depends(get_current_admin_user)]
):
    """Register a new user (admin only)"""
    # Check if username already exists
    if get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )

    # Check if email already exists
    if get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create user
    user = create_user_in_db(user_data)

    logger.info(f"Admin {current_admin['username']} created new user: {user_data.username} with role: {user_data.role}")

    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        role=user["role"],
        is_active=user["is_active"],
        created_at=datetime.fromisoformat(user["created_at"])
    )


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Login endpoint to get access token"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: Annotated[dict, Depends(get_current_active_user)]):
    """Get current user information"""
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"],
        is_active=current_user["is_active"],
        created_at=datetime.fromisoformat(current_user["created_at"]),
        first_name=current_user.get("first_name") or "",
        last_name=current_user.get("last_name") or "",
    )


@app.put("/users/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Update current user information (email only for non-admins)"""
    if user_update.email:
        # Check if email is already taken by another user
        existing_user = get_user_by_email(user_update.email)
        if existing_user and existing_user["username"] != current_user["username"]:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        # Only allow role changes for admins changing their own role
        if user_update.role and not is_admin(current_user):
            raise HTTPException(
                status_code=403,
                detail="Only admins can change roles"
            )

        update_user_info(current_user["username"], user_update.email, user_update.role)

    # Get updated user
    updated_user = get_user_by_username(current_user["username"])

    return UserResponse(
        id=updated_user["id"],
        username=updated_user["username"],
        email=updated_user["email"],
        role=updated_user["role"],
        is_active=updated_user["is_active"],
        created_at=datetime.fromisoformat(updated_user["created_at"]),
        first_name=updated_user.get("first_name") or "",
        last_name=updated_user.get("last_name") or "",
    )


@app.post("/users/me/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Change current user password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user["hashed_password"]):
        raise HTTPException(
            status_code=400,
            detail="Incorrect current password"
        )

    # Update password
    update_user_password(current_user["username"], password_data.new_password)

    return {"message": "Password updated successfully"}


@app.get("/users/me/profile")
async def get_my_profile(current_user: Annotated[dict, Depends(get_current_active_user)]):
    """Get current user profile (first_name, last_name, email)"""
    return {
        "first_name": current_user.get("first_name") or "",
        "last_name": current_user.get("last_name") or "",
        "email": current_user.get("email") or "",
    }


@app.put("/users/me/profile")
async def update_my_profile(
    profile: ProfileUpdate,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Update current user profile"""
    if profile.email:
        existing = get_user_by_email(profile.email)
        if existing and existing["id"] != current_user["id"]:
            raise HTTPException(status_code=400, detail="Email already in use")
    update_user_profile(current_user["username"], profile.first_name, profile.last_name, profile.email)
    return {"message": "Profile updated successfully"}


@app.delete("/users/me")
async def deactivate_current_user(current_user: Annotated[dict, Depends(get_current_active_user)]):
    """Deactivate current user account"""
    deactivate_user(current_user["username"])
    return {"message": "Account deactivated successfully"}


# Admin endpoints
@app.get("/admin/users", response_model=list[UserResponse])
async def get_all_users_admin(current_admin: Annotated[dict, Depends(get_current_admin_user)]):
    """Get all users (admin only)"""
    users = get_all_users()

    return [
        UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            role=user["role"],
            is_active=user["is_active"],
            created_at=datetime.fromisoformat(user["created_at"])
        )
        for user in users
    ]


@app.put("/admin/users/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: int,
    user_update: UserUpdate,
    current_admin: Annotated[dict, Depends(get_current_admin_user)]
):
    """Update user information (admin only)"""
    # Get the user to update
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if email is already taken by another user
    if user_update.email:
        existing_user = get_user_by_email(user_update.email)
        if existing_user and existing_user["id"] != user_id:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

    # Update user
    update_user_info_by_id(user_id, user_update.email, user_update.role)

    # Get updated user
    updated_user = get_user_by_id(user_id)

    logger.info(f"Admin {current_admin['username']} updated user {user['username']}")

    return UserResponse(
        id=updated_user["id"],
        username=updated_user["username"],
        email=updated_user["email"],
        role=updated_user["role"],
        is_active=updated_user["is_active"],
        created_at=datetime.fromisoformat(updated_user["created_at"]),
        first_name=updated_user.get("first_name") or "",
        last_name=updated_user.get("last_name") or "",
    )


@app.post("/admin/users/{user_id}/change-password")
async def admin_change_user_password(
    user_id: int,
    password_data: AdminPasswordChange,
    current_admin: Annotated[dict, Depends(get_current_admin_user)]
):
    """Change user password (admin only)"""
    # Check if user exists
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update password
    update_user_password_by_id(user_id, password_data.new_password)

    logger.info(f"Admin {current_admin['username']} changed password for user {user['username']}")

    return {"message": "Password updated successfully"}


@app.post("/admin/users/{user_id}/deactivate")
async def admin_deactivate_user(
    user_id: int,
    current_admin: Annotated[dict, Depends(get_current_admin_user)]
):
    """Deactivate user (admin only)"""
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from deactivating themselves
    if user_id == current_admin["id"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate your own account"
        )

    deactivate_user_by_id(user_id)

    logger.info(f"Admin {current_admin['username']} deactivated user {user['username']}")

    return {"message": "User deactivated successfully"}


@app.post("/admin/users/{user_id}/activate")
async def admin_activate_user(
    user_id: int,
    current_admin: Annotated[dict, Depends(get_current_admin_user)]
):
    """Activate user (admin only)"""
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    activate_user_by_id(user_id)

    logger.info(f"Admin {current_admin['username']} activated user {user['username']}")

    return {"message": "User activated successfully"}


@app.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: int,
    current_admin: Annotated[dict, Depends(get_current_admin_user)]
):
    """Permanently delete user (admin only)"""
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from deleting themselves
    if user_id == current_admin["id"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )

    # Check if this is the last active admin
    if user["role"] == "admin" and user["is_active"]:
        # Count active admins
        all_users = get_all_users()
        active_admin_count = sum(1 for u in all_users if u["role"] == "admin" and u["is_active"] and u["id"] != user_id)
        
        if active_admin_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the last active admin user"
            )

    success = delete_user_by_id(user_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user")

    logger.info(f"Admin {current_admin['username']} deleted user {user['username']} (ID: {user_id})")

    return {"message": "User deleted successfully"}


# Report generation endpoints
def update_compilation_status(comp_id: str, progress: int, step: str, status: str = "running"):
    """Update the compilation status for a given compilation ID"""
    with compilation_lock:
        if comp_id in compilation_status:
            compilation_status[comp_id].update({
                'progress': progress,
                'current_step': step,
                'status': status,
                'last_updated': datetime.now()
            })


def apply_background_to_pdf(pdf_path: Path, background_pdf_path: Path) -> None:
    """Overlay cycling background pages on content pages of a PDF (skip first and last)."""
    try:
        import fitz
    except ImportError:
        logger.warning("PyMuPDF not available; skipping background overlay")
        return
    if not background_pdf_path.exists():
        return
    try:
        main_doc = fitz.open(str(pdf_path))
        bg_doc = fitz.open(str(background_pdf_path))
        n = main_doc.page_count
        num_bg = bg_doc.page_count
        if n <= 2 or num_bg == 0:
            bg_doc.close()
            main_doc.close()
            return
        new_doc = fitz.open()
        for i in range(n):
            page = main_doc[i]
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            if 1 <= i <= n - 2:
                bg_idx = (i - 1) % num_bg
                new_page.show_pdf_page(new_page.rect, bg_doc, bg_idx)
            new_page.show_pdf_page(new_page.rect, main_doc, i)
        bg_doc.close()
        main_doc.close()
        new_doc.save(str(pdf_path))
        new_doc.close()
        logger.info(f"Applied background overlay to {pdf_path.name}")
    except Exception as e:
        logger.error(f"Background overlay failed for {pdf_path}: {e}")


def render_html_to_pdf(project_dir: Path, output_dir: Path, comp_id: str) -> list[Optional[Path]]:
    """
    Render report.html / biblio.html → PDF via WeasyPrint.
    Returns [report_pdf_path_or_None, biblio_pdf_path_or_None].
    """
    with compilation_lock:
        if compilation_status.get(comp_id, {}).get('status') == 'cancelled':
            return [None, None]

    from dibisoreporting import DibisoReporting
    import markdown

    update_compilation_status(comp_id, 72, "Rendering HTML report...")

    # Load analyses from DB and convert Markdown → HTML
    user_id = compilation_status[comp_id].get('user_id')
    raw_analyses = get_analyses(comp_id, user_id) if user_id else {}
    analyses_html = {k: markdown.markdown(v) for k, v in raw_analyses.items() if v}

    try:
        DibisoReporting.render_from_saved(str(project_dir), analyses_html)
    except Exception as e:
        logger.error(f"Jinja2 render failed for {comp_id}: {e}")
        update_compilation_status(comp_id, 0, f"Report rendering failed: {e}", "failed")
        return [None, None]

    try:
        from weasyprint import HTML as WeasyprintHTML
    except OSError as e:
        logger.warning(f"WeasyPrint unavailable (missing system library: {e}). "
                       "HTML files will be available but no PDF will be generated. "
                       "Install the GTK3 runtime (see README_RUN.md) to enable PDF export.")
        # Copy HTML files to output dir so they can still be downloaded via ZIP
        for name in ("report", "biblio"):
            html_path = project_dir / f"{name}.html"
            if html_path.exists():
                shutil.copy2(str(html_path), str(output_dir / f"{name}.html"))
        return [None, None]

    results = []
    for name, progress in [("report", 80), ("biblio", 88)]:
        html_path = project_dir / f"{name}.html"
        if not html_path.exists():
            results.append(None)
            continue
        with compilation_lock:
            if compilation_status.get(comp_id, {}).get('status') == 'cancelled':
                return [None, None]
        update_compilation_status(comp_id, progress, f"Converting {name}.html to PDF...")
        try:
            pdf_path = output_dir / f"{name}.pdf"
            WeasyprintHTML(filename=str(html_path)).write_pdf(str(pdf_path), presentational_hints=True)
            if html_template_path:
                bg_path = Path(html_template_path) / "dibiso-html" / "assets" / "background.pdf"
                apply_background_to_pdf(pdf_path, bg_path)
            # Also copy HTML to output dir for download
            shutil.copy2(str(html_path), str(output_dir / f"{name}.html"))
            results.append(pdf_path)
        except Exception as e:
            logger.error(f"WeasyPrint failed for {name}: {e}")
            results.append(None)

    return results


def create_zip_archive(project_folder: Path, zip_path: Path) -> bool:
    """
    Create a ZIP archive of the project folder.
    Returns True if successful, False otherwise.
    """
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in project_folder.rglob('*'):
                if file_path.is_file():
                    # Add file to zip with relative path
                    arcname = file_path.relative_to(project_folder)
                    zipf.write(file_path, arcname)
        return True
    except Exception as e:
        logger.error(f"Failed to create ZIP archive: {e}")
        return False


def generate_report_project(comp_id: str, request_data: ReportRequest) -> Optional[Path]:
    """Generate HTML report project with error handling and cancellation support."""
    # Check if cancelled before starting
    with compilation_lock:
        if compilation_status.get(comp_id, {}).get('status') == 'cancelled':
            return None
    update_compilation_status(comp_id, 10, "Fetching data and making plots (this step may take a while...)")
    # Create temporary directory for the project
    project_dir = Path(tempfile.mkdtemp(prefix="html_output_"))
    try:
        logger.info("Starting subprocess for data fetching with parameters:")
        logger.info(f"  Entity ID: {request_data.entity_id}")
        logger.info(f"  Year: {request_data.year}")
        logger.info(f"  Entity Acronym: {request_data.entity_acronym}")
        logger.info(f"  Entity Full Name: {request_data.entity_full_name}")
        logger.info(f"  Max entities: {request_data.max_entities}")

        # Start the data fetching + report generation as a subprocess with dynamic parameters
        import json as _json
        _cwd = _json.dumps(os.getcwd())
        _cache = _json.dumps(str(openalex_analysis_cache_path))
        _key = _json.dumps(str(openalex_api_key))
        _email = _json.dumps(str(openalex_email))
        _project_dir = _json.dumps(str(project_dir))
        _html_tpl = _json.dumps(str(html_template_url))
        _html_path = _json.dumps(str(html_template_path))
        _scanr_pwd = _json.dumps(str(scanr_api_password))
        _scanr_url = _json.dumps(str(scanr_api_url))
        _scanr_user = _json.dumps(str(scanr_api_username))
        _scanr_bso = _json.dumps(str(scanr_bso_index))
        _scanr_pub = _json.dumps(str(scanr_publications_index))
        _acronym = _json.dumps(request_data.entity_acronym)
        _fullname = _json.dumps(request_data.entity_full_name)
        _entity_id = _json.dumps(request_data.entity_id)
        _reporter = _json.dumps(request_data.reporter)
        _reporter_email = _json.dumps(request_data.reporter_email)
        process = subprocess.Popen([
            sys.executable, '-c',
            f'''
import sys
sys.path.insert(0, {_cwd})

from openalex_analysis.data import config as openalex_analysis_config
from dibisoreporting import Biso

if {_cache} != "None":
    openalex_analysis_config.project_data_folder_path = {_cache}
if {_key} != "None":
    openalex_analysis_config.api_key = {_key}
if {_email} != "None":
    openalex_analysis_config.email = {_email}


biso_reporting = Biso(
    {_entity_id},
    {request_data.year},
    entity_acronym={_acronym},
    entity_full_name={_fullname},
    html_template_path={_html_path} if {_html_path} != "None" else None,
    html_template_url={_html_tpl} if {_html_path} == "None" else None,
    max_entities={request_data.max_entities},
    root_path={_project_dir},
    reporter={_reporter},
    reporter_email={_reporter_email},
    watermark_text="",
    scanr_api_password={_scanr_pwd},
    scanr_api_url={_scanr_url},
    scanr_api_username={_scanr_user},
    scanr_bso_index={_scanr_bso},
    scanr_publications_index={_scanr_pub},
)
biso_reporting.generate_report()
            '''
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Store the process reference for cancellation
        with process_lock:
            data_fetching_processes[comp_id] = process

        # Wait for completion with timeout and cancellation checks
        start_time = time.time()
        timeout_seconds = data_fetching_timeout_seconds
        while process.poll() is None:
            # Check for timeout
            if time.time() - start_time > timeout_seconds:
                logger.error(f"Process timeout after {timeout_seconds} seconds for {comp_id}")
                try:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                except Exception as e:
                    logger.error(f"Error terminating timed out process: {e}")
                # Clean up and return early
                if project_dir.exists():
                    shutil.rmtree(project_dir)
                # with compilation_lock:
                if compilation_status.get(comp_id, {}).get('status') != 'cancelled':
                    update_compilation_status(comp_id, 0, "Process timeout - data fetching took too long", "failed")
                return None

            # Check for cancellation
            with compilation_lock:
                if compilation_status.get(comp_id, {}).get('status') == 'cancelled':
                    try:
                        process.terminate()
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                        logger.info(f"Terminated data fetching process for {comp_id}")
                    except Exception as e:
                        logger.error(f"Error terminating data fetching process: {e}")
                    # Clean up and return early
                    if project_dir.exists():
                        shutil.rmtree(project_dir)
                    return None
            time.sleep(0.5)  # Check every 500ms

        # Get results
        try:
            stdout, stderr = process.communicate(timeout=10)  # 10 second timeout for communication
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout waiting for process communication for {comp_id}")
            process.kill()
            stdout, stderr = process.communicate()

        logger.info("Subprocess stdout: " + stdout)
        if stderr:
            logger.error("Subprocess stderr: " + stderr)

        # Remove process reference immediately
        with process_lock:
            data_fetching_processes.pop(comp_id, None)

        # Check return code and handle failure immediately
        if process.returncode != 0:
            logger.error(f"Data fetching failed with return code {process.returncode}")
            logger.info(f"Cleaning up the generated project")
            if project_dir.exists():
                try:
                    shutil.rmtree(project_dir)
                except Exception as e:
                    logger.error(f"Error cleaning up project dir: {e}")
            logger.info("Update status to failed")
            # with compilation_lock:
            if compilation_status.get(comp_id, {}).get('status') != 'cancelled':
                error_msg = "Data fetching failed"
                if "JSONDecodeError" in stderr:
                    error_msg = ("Data fetching failed due to a JSON decode error. "
                                 "This might occur if the server response is empty or malformed. "
                                 "Please check the HAL collection ID or contact your admin.")
                elif "ConnectionError" in stderr:
                    error_msg = "Data fetching failed - network connection error"
                elif "TimeoutError" in stderr:
                    error_msg = "Data fetching failed - request timeout"
                logger.info(error_msg)
                update_compilation_status(comp_id, 0, error_msg, "failed")
            logger.info("Return, don't continue processing")
            return None

        # Final cancellation check before returning success
        with compilation_lock:
            if compilation_status.get(comp_id, {}).get('status') == 'cancelled':
                if project_dir.exists():
                    shutil.rmtree(project_dir)
                return None
        logger.info(f"Data fetching completed successfully for {comp_id}")
        return project_dir
    except subprocess.TimeoutExpired:
        logger.error(f"Subprocess timed out for {comp_id}")
        if project_dir.exists():
            shutil.rmtree(project_dir)
        # with compilation_lock:
        if compilation_status.get(comp_id, {}).get('status') != 'cancelled':
            update_compilation_status(comp_id, 0, "Data fetching timeout", "failed")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in project generation for {comp_id}: {e}")
        if project_dir.exists():
            try:
                shutil.rmtree(project_dir)
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {cleanup_error}")
        # with compilation_lock:
        if compilation_status.get(comp_id, {}).get('status') != 'cancelled':
            update_compilation_status(comp_id, 0, f"Generation error: {str(e)}", "failed")
        return None



def run_compilation(comp_id: str, request_data: ReportRequest):
    """Run the compilation with improved error handling and early exits"""
    try:
        # Initial status update
        update_compilation_status(comp_id, 2, "Checking HAL collection ID...")

        # check that the HAL collection ID is valid
        url = f"https://api.archives-ouvertes.fr/search/?q=collCode_s:{request_data.entity_id}&wt=json&rows=0"
        coll_exists = requests.get(url).json().get('response',{}).get('numFound', 0) > 0
        if not coll_exists:
            logging.info(f"Collection ID {request_data.entity_id} does not exist in HAL. Aborting report generation.")
            update_compilation_status(comp_id, 0, "The HAL collection ID doesn't exist", "failed")
            return

        update_compilation_status(comp_id, 5, "Starting generation process...")

        # Check for cancellation immediately
        with compilation_lock:
            if compilation_status.get(comp_id, {}).get('status') == 'cancelled':
                logger.info(f"Compilation {comp_id} cancelled during initialization.")
                return

        # Generate the report project (data fetching + figure generation, long-running)
        logger.info(f"Generating report project for {comp_id}...")
        project_folder = generate_report_project(comp_id, request_data)

        # CRITICAL: Exit immediately if project generation failed or was cancelled
        if project_folder is None:
            logger.info(f"Project generation failed or was cancelled for {comp_id}, exiting compilation")
            return

        # Store project_dir so export endpoint can find figures/context JSON
        with compilation_lock:
            compilation_status[comp_id]['project_dir'] = str(project_folder)

        # Check if compilation was cancelled after project generation
        with compilation_lock:
            if compilation_status.get(comp_id, {}).get('status') == 'cancelled':
                logger.info(f"Compilation {comp_id} cancelled after project generation.")
                if project_folder.exists():
                    try:
                        shutil.rmtree(project_folder)
                    except Exception as e:
                        logger.error(f"Error cleaning up project folder: {e}")
                return

        # Create temporary directory for outputs
        temp_dir = Path(tempfile.mkdtemp(prefix="html_output_"))

        # Render HTML → PDF via WeasyPrint
        logger.info(f"Rendering HTML report for {comp_id} in {project_folder}")
        pdf_paths = render_html_to_pdf(project_folder, temp_dir, comp_id)

        # Check for cancellation before creating ZIP
        with compilation_lock:
            if compilation_status.get(comp_id, {}).get('status') == 'cancelled':
                logger.info(f"Compilation {comp_id} cancelled before ZIP creation.")
                cleanup_directories(project_folder, temp_dir)
                return

        update_compilation_status(comp_id, 98, "Creating ZIP archive...")

        # Create ZIP archive (always, even if PDF compilation failed)
        zip_path = temp_dir / "project.zip"
        logger.info(f"Creating ZIP archive at {zip_path} for {comp_id}")

        if not create_zip_archive(project_folder, zip_path):
            # with compilation_lock:
            if compilation_status.get(comp_id, {}).get('status') != 'cancelled':
                update_compilation_status(comp_id, 0, "Failed to create ZIP archive", "failed")
            cleanup_directories(project_folder, temp_dir)
            return

        # render_html_to_pdf writes PDFs directly into temp_dir, so pdf_paths already
        # point to temp_dir/report.pdf and temp_dir/biblio.pdf — no copy needed.
        compilation_successful = None not in pdf_paths

        # Keep project_folder alive for the session so /report-sections and /figures
        # endpoints can serve figure previews and section metadata to the edit view.
        # The cleanup task (cleanup_old_compilations) will remove it after
        # PROJECTS_PERSISTENCE_TIME_HOURS hours.

        # Final check for cancellation before marking as completed
        with compilation_lock:
            if compilation_status.get(comp_id, {}).get('status') == 'cancelled':
                logger.info(f"Compilation {comp_id} cancelled before final status update.")
                if temp_dir.exists():
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception as e:
                        logger.error(f"Error cleaning up temp dir: {e}")
                return

            # Mark as completed or partial success
            if compilation_status.get(comp_id, {}).get('status') == 'running':
                if compilation_successful:
                    # Full success
                    compilation_status[comp_id].update({
                        'progress': 100,
                        'current_step': 'Compilation completed successfully!',
                        'status': 'completed',
                        'result': {
                            'message': f'Report generated successfully for {request_data.entity_acronym} '
                                       f'({request_data.year})',
                            'pdf_url': '/download-pdf',
                            'zip_url': '/download-zip',
                            'compilation_id': comp_id
                        },
                        'temp_dir': str(temp_dir),
                        'last_updated': datetime.now()
                    })
                else:
                    # Partial success - data and ZIP available, but PDF compilation failed
                    compilation_status[comp_id].update({
                        'progress': 100,
                        'current_step': 'PDF generation failed, but project files are available',
                        'status': 'partial',
                        'result': {
                            'message': f'Data fetched for {request_data.entity_acronym} ({request_data.year}), '
                                       f'but PDF generation failed. You can download the project files.',
                            'pdf_url': None,
                            'zip_url': '/download-zip',
                            'compilation_id': comp_id,
                            'warning': 'PDF generation failed. Download the ZIP to open the HTML report in a browser.'
                        },
                        'temp_dir': str(temp_dir),
                        'last_updated': datetime.now()
                    })
            else:
                logger.warning(
                    f"Compilation {comp_id} not marked as completed because status is "
                    f"{compilation_status[comp_id]['status']}"
                )

        logger.info(f"Report generation completed for {comp_id} (successful: {compilation_successful})")

    except Exception as e:
        logger.error(f"Critical error in background compilation for {comp_id}: {e}")
        # with compilation_lock:
        if compilation_status.get(comp_id, {}).get('status') != 'cancelled':
            update_compilation_status(comp_id, 0, f"Compilation error: {str(e)}", "failed")


def cleanup_directories(*dirs):
    """Helper function to safely clean up directories"""
    for directory in dirs:
        if directory and Path(directory).exists():
            try:
                shutil.rmtree(directory)
            except Exception as e:
                logger.error(f"Error cleaning up directory {directory}: {e}")


def verify_and_get_file_path(temp_id: str, current_user: dict, filename: str) -> Path:
    """
    Verify that the current user owns the file associated with temp_id and return the file path.
    Returns the file path if valid and exists, raises HTTPException otherwise.
    """
    # temp_id is actually the compilation_id, find the compilation and verify ownership
    compilation_owner = None
    temp_dir_str = None
    with compilation_lock:
        if temp_id in compilation_status:
            status = compilation_status[temp_id]
            if status.get('user_id') == current_user["id"]:
                compilation_owner = current_user["id"]
                temp_dir_str = status.get('temp_dir')
    
    if not compilation_owner or not temp_dir_str:
        raise HTTPException(
            status_code=403, 
            detail="Access denied - file not found or you don't own this file"
        )
    
    temp_dir = Path(temp_dir_str)
    file_path = temp_dir / filename
    
    if not file_path.exists():
        file_type = filename.split('.')[-1].upper()
        raise HTTPException(status_code=404, detail=f"{file_type} file not found")
    
    return file_path


async def run_compilation_async(comp_id: str, request_data: ReportRequest):
    """Run the compilation process in the background without blocking the event loop"""
    loop = asyncio.get_event_loop()
    # The actual blocking work is done inside run_compilation, which is run in the thread_pool
    await loop.run_in_executor(thread_pool, run_compilation, comp_id, request_data)


# ── Analyses & export endpoints ─────────────────────────────────────────────

class AnalysisUpdate(BaseModel):
    content: str


def _get_comp_project_dir(comp_id: str, current_user: dict) -> Path:
    """Shared ownership check + return project_dir path."""
    with compilation_lock:
        status = compilation_status.get(comp_id)
    if not status:
        raise HTTPException(status_code=404, detail="Compilation not found")
    if status.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="Access denied")
    project_dir = status.get('project_dir')
    if not project_dir or not Path(project_dir).exists():
        raise HTTPException(status_code=404, detail="Project files not available")
    return Path(project_dir)


@app.get("/report-sections/{comp_id}")
async def get_report_sections(
    comp_id: str,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Return the list of editable sections for a completed report."""
    project_dir = _get_comp_project_dir(comp_id, current_user)
    figures_json = project_dir / "figures.json"
    context_json = project_dir / "context.json"
    if not figures_json.exists() or not context_json.exists():
        raise HTTPException(status_code=404, detail="Report data not available yet")

    import json
    with open(figures_json, encoding="utf-8") as f:
        generated_figures: set = set(json.load(f).keys())
    with open(context_json, encoding="utf-8") as f:
        context = json.load(f)
    report_type = context.get("report_type", "biso")
    all_sections = REPORT_SECTIONS.get(report_type, REPORT_SECTIONS["biso"])

    result = []
    for sec in all_sections:
        has_figure = sec.get("figure", True)
        if not has_figure or sec["id"] in generated_figures:
            result.append({"id": sec["id"], "label": sec["label"], "has_figure": has_figure and sec["id"] in generated_figures})
    return result


@app.get("/analyses/{comp_id}")
async def get_analyses_endpoint(
    comp_id: str,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Return all saved analyses for a report as {section_id: markdown_content}."""
    with compilation_lock:
        status = compilation_status.get(comp_id)
    if not status:
        raise HTTPException(status_code=404, detail="Compilation not found")
    if status.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="Access denied")
    return get_analyses(comp_id, current_user['id'])


@app.put("/analyses/{comp_id}/{section_id}")
async def save_analysis_endpoint(
    comp_id: str,
    section_id: str,
    body: AnalysisUpdate,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Upsert a single section analysis (auto-save target)."""
    with compilation_lock:
        status = compilation_status.get(comp_id)
    if not status:
        raise HTTPException(status_code=404, detail="Compilation not found")
    if status.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="Access denied")
    upsert_analysis(comp_id, current_user['id'], section_id, body.content)
    return {"message": "saved"}


@app.get("/figures/{comp_id}/{figure_name}")
async def get_figure_svg(
    comp_id: str,
    figure_name: str,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Serve an SVG figure file for preview in the editor."""
    project_dir = _get_comp_project_dir(comp_id, current_user)
    svg_path = project_dir / "figures" / f"{figure_name}.svg"
    if not svg_path.exists():
        raise HTTPException(status_code=404, detail="Figure not found")
    return FileResponse(str(svg_path), media_type="image/svg+xml")


@app.post("/export/{comp_id}")
async def export_report(
    comp_id: str,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Re-render report with current analyses and produce PDF via WeasyPrint."""
    project_dir = _get_comp_project_dir(comp_id, current_user)

    with compilation_lock:
        status = compilation_status.get(comp_id)
        temp_dir_str = status.get('temp_dir')
        status['export_status'] = 'rendering'
        status['last_updated'] = datetime.now()

    temp_dir = Path(temp_dir_str) if temp_dir_str else Path(tempfile.mkdtemp(prefix="html_output_"))

    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        thread_pool,
        _do_export, comp_id, current_user['id'], project_dir, temp_dir
    )
    return {"message": "Export started", "comp_id": comp_id}


def _convert_svg_style_to_attrs(html_content: str) -> str:
    """Move SVG presentation properties from inline style= to SVG element attributes.

    WeasyPrint 68 parses inline style= via its CSS engine, which rejects SVG-specific
    properties (fill, stroke, etc.) as unknown. Moving them to presentation attributes
    fixes rendering of Plotly-generated inline SVGs.
    """
    import re as _re

    SVG_PROPS = frozenset([
        'fill', 'fill-opacity', 'fill-rule',
        'stroke', 'stroke-opacity', 'stroke-width',
        'stroke-dasharray', 'stroke-dashoffset',
        'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit',
        'vector-effect', 'clip-rule', 'clip-path',
        'stop-color', 'stop-opacity',
        'paint-order', 'shape-rendering',
        'marker-start', 'marker-mid', 'marker-end',
    ])

    def process_element(match):
        full_tag = match.group(0)
        style_m = _re.search(r'\sstyle="([^"]*)"', full_tag)
        if not style_m:
            return full_tag
        # Preserve self-closing tags — stripping '/' turns <path/> into an unclosed element
        # which swallows all subsequent siblings (including text labels) as invisible children.
        is_self_closing = full_tag.rstrip().endswith('/>')
        close = '/>' if is_self_closing else '>'
        style_str = style_m.group(1)
        css_parts = []
        new_attrs = {}
        for part in style_str.split(';'):
            part = part.strip()
            if not part:
                continue
            prop, _, val = part.partition(':')
            prop = prop.strip()
            val = val.strip()
            if prop in SVG_PROPS:
                if prop == 'stroke-width' and val.endswith('px'):
                    val = val[:-2]
                new_attrs[prop] = val
            else:
                css_parts.append(f'{prop}: {val}')
        new_style = '; '.join(css_parts)
        updated_tag = full_tag.replace(style_m.group(0), f' style="{new_style}"' if new_style else '')
        for attr, val in new_attrs.items():
            if f' {attr}=' not in updated_tag:
                updated_tag = updated_tag.rstrip('>').rstrip('/').rstrip() + f' {attr}="{val}"{close}'
        return updated_tag

    def process_svg_block(svg_match):
        svg_content = svg_match.group(0)
        svg_content = _re.sub(
            r'<(?:path|rect|circle|ellipse|line|polyline|polygon|text|tspan|g|use|'
            r'symbol|marker|stop|linearGradient|radialGradient|pattern|defs|clipPath)\b[^>]*>',
            process_element,
            svg_content,
        )
        return svg_content

    return _re.sub(r'<svg\b.*?</svg>', process_svg_block, html_content, flags=_re.DOTALL)


def _inline_assets_in_html(html_content: str, project_dir: Path) -> str:
    """Replace CSS <link> tags with inline <style> blocks and image src with base64 data URIs."""
    import base64
    import re as _re
    template_dir = project_dir / "dibiso-html"
    # Fallback to global template mount so assets added after project generation still inline
    global_template_dir = (Path(html_template_path) / "dibiso-html") if html_template_path else None

    def _resolve(relative: str) -> Path | None:
        # Prefer global mount (always current) over project copy (may be stale from generation time)
        if global_template_dir:
            p2 = global_template_dir / relative
            if p2.exists():
                return p2
        p = template_dir / relative
        if p.exists():
            return p
        return None

    def replace_css_link(match):
        href = _re.search(r'href="([^"]+)"', match.group(0))
        if not href:
            return match.group(0)
        css_path = _resolve(href.group(1))
        if css_path:
            return f'<style>\n{css_path.read_text(encoding="utf-8")}\n</style>'
        return match.group(0)

    html_content = _re.sub(r'<link[^>]+rel="stylesheet"[^>]*>', replace_css_link, html_content)

    def replace_img_src(match):
        src_match = _re.search(r'src="([^"]+)"', match.group(0))
        if not src_match:
            return match.group(0)
        src = src_match.group(1)
        if src.startswith(('data:', 'http:', 'https:')):
            return match.group(0)
        img_path = _resolve(src)
        if img_path:
            mime = 'image/svg+xml' if src.endswith('.svg') else 'image/png'
            b64 = base64.b64encode(img_path.read_bytes()).decode('ascii')
            return match.group(0).replace(f'src="{src}"', f'src="data:{mime};base64,{b64}"')
        return match.group(0)

    html_content = _re.sub(r'<img\b[^>]*>', replace_img_src, html_content)
    html_content = _convert_svg_style_to_attrs(html_content)
    return html_content


def _do_export(comp_id: str, user_id: int, project_dir: Path, output_dir: Path):
    """Background export task: render Jinja2 → HTML (always), then WeasyPrint → PDF (if GTK available)."""
    import markdown as md_lib
    from dibisoreporting import DibisoReporting

    # Step 1: Re-render HTML with current analyses
    try:
        raw_analyses = get_analyses(comp_id, user_id)
        analyses_html = {k: md_lib.markdown(v) for k, v in raw_analyses.items() if v}
        DibisoReporting.render_from_saved(str(project_dir), analyses_html)
    except Exception as e:
        logger.error(f"Render failed for export {comp_id}: {e}")
        with compilation_lock:
            if comp_id in compilation_status:
                compilation_status[comp_id]['export_status'] = 'failed'
                compilation_status[comp_id]['last_updated'] = datetime.now()
        return

    # Step 2: Inline CSS+assets → self-contained HTML in output dir
    html_urls = {}
    for name in ("report", "biblio"):
        html_path = project_dir / f"{name}.html"
        if html_path.exists():
            inlined = _inline_assets_in_html(html_path.read_text(encoding="utf-8"), project_dir)
            out_path = output_dir / f"{name}.html"
            out_path.write_text(inlined, encoding="utf-8")
            html_urls[name] = f"/download-html?temp_id={comp_id}&file_name={name}"

    # Step 3: PDF via WeasyPrint using the inlined HTML so CSS is resolved
    pdf_urls = {}
    try:
        from weasyprint import HTML as WeasyprintHTML
        for name in ("report", "biblio"):
            inlined_path = output_dir / f"{name}.html"
            if not inlined_path.exists():
                continue
            try:
                pdf_path = output_dir / f"{name}.pdf"
                WeasyprintHTML(filename=str(inlined_path)).write_pdf(str(pdf_path), presentational_hints=True)
                if html_template_path:
                    bg_path = Path(html_template_path) / "dibiso-html" / "assets" / "background.pdf"
                    apply_background_to_pdf(pdf_path, bg_path)
                pdf_urls[name] = f"/download-pdf?temp_id={comp_id}&file_name={name}"
            except Exception as e:
                logger.error(f"WeasyPrint failed for {name} in export {comp_id}: {e}")
    except OSError as e:
        logger.warning(f"WeasyPrint unavailable for export {comp_id} (GTK missing): {e}")

    # Step 4: Copy inlined HTML back to project_dir then create ZIP so it includes the styled files
    zip_url = None
    try:
        for name in ("report", "biblio"):
            inlined_path = output_dir / f"{name}.html"
            if inlined_path.exists():
                shutil.copy2(str(inlined_path), str(project_dir / f"{name}.html"))
        zip_path = output_dir / "project.zip"
        create_zip_archive(project_dir, zip_path)
        zip_url = f"/download-zip?temp_id={comp_id}"
    except Exception as e:
        logger.error(f"ZIP creation failed for export {comp_id}: {e}")

    with compilation_lock:
        if comp_id in compilation_status:
            compilation_status[comp_id].update({
                'export_status': 'done',
                'export_pdf_url': pdf_urls.get('report'),
                'export_html_url': html_urls.get('report'),
                'export_biblio_html_url': html_urls.get('biblio'),
                'export_zip_url': zip_url,
                'temp_dir': str(output_dir),
                'last_updated': datetime.now(),
            })


@app.get("/download-html")
async def download_html(
    temp_id: str,
    file_name: str,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Download the generated HTML report file."""
    with compilation_lock:
        status = compilation_status.get(temp_id)
    if not status:
        raise HTTPException(status_code=404, detail="Compilation not found")
    if status.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="Access denied")
    temp_dir = status.get('temp_dir')
    if not temp_dir:
        raise HTTPException(status_code=404, detail="Output directory not available")
    html_path = Path(temp_dir) / f"{file_name}.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="HTML file not found")
    return FileResponse(
        path=str(html_path),
        filename=f"{file_name}.html",
        media_type="text/html"
    )


# ────────────────────────────────────────────────────────────────────────────

@app.post("/generate-report")
async def generate_report_endpoint(
    request: ReportRequest,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """
    Start report generation with the provided parameters and return a compilation ID for progress tracking.
    Requires authentication.
    """
    # Validate the request (Pydantic will handle basic validation)
    logger.info(f"Received report generation request from user {current_user['username']}: {request.dict()}")

    # Generate unique compilation ID
    comp_id = str(uuid.uuid4())

    # Initialize compilation status
    with compilation_lock:
        compilation_status[comp_id] = {
            'progress': 0,
            'current_step': 'Initializing...',
            'status': 'running',
            'request_data': request.dict(),  # Store request data for reference
            'user_id': current_user["id"],  # Store user who initiated the request
            'username': current_user["username"],
            'created_at': datetime.now(),
            'last_updated': datetime.now()
        }

    # Start background compilation as a task instead of using BackgroundTasks
    asyncio.create_task(run_compilation_async(comp_id, request))

    return {
        "message": f"Generation started for {request.entity_acronym} ({request.year})",
        "compilation_id": comp_id,
        "parameters": {
            "year": request.year,
            "entity_acronym": request.entity_acronym,
            "entity_full_name": request.entity_full_name,
            "entity_id": request.entity_id
        }
    }


@app.get("/compilation-status/{comp_id}")
async def get_compilation_status(
    comp_id: str,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Get the current status of a compilation. Users can only see their own compilations."""
    with compilation_lock:
        if comp_id not in compilation_status:
            raise HTTPException(status_code=404, detail="Compilation ID not found")

        status = compilation_status[comp_id]

        # Check if user owns this compilation
        if status.get('user_id') != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied to this compilation")

        status_copy = status.copy()

    # Remove internal fields from response
    status_copy.pop('temp_dir', None)
    status_copy.pop('result', None)
    status_copy.pop('created_at', None)
    status_copy.pop('last_updated', None)
    status_copy.pop('request_data', None)
    status_copy.pop('user_id', None)
    status_copy.pop('project_dir', None)

    # Expose export progress fields
    # export_status and export_pdf_url are kept if present

    return status_copy


@app.get("/compilation-result/{comp_id}")
async def get_compilation_result(
    comp_id: str,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Get the result of a completed compilation. Users can only see their own compilations."""
    with compilation_lock:
        if comp_id not in compilation_status:
            raise HTTPException(status_code=404, detail="Compilation ID not found")

        status = compilation_status[comp_id]

        # Check if user owns this compilation
        if status.get('user_id') != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied to this compilation")

        if status['status'] != 'completed':
            raise HTTPException(status_code=400, detail="Compilation not completed yet")

        if 'result' not in status:
            raise HTTPException(status_code=500, detail="Compilation result not available")

    return status['result']


@app.post("/cancel-compilation/{comp_id}")
async def cancel_compilation(
    comp_id: str,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Cancel a running compilation. Users can only cancel their own compilations."""
    with compilation_lock:
        if comp_id not in compilation_status:
            raise HTTPException(status_code=404, detail="Compilation ID not found")

        status = compilation_status[comp_id]

        # Check if user owns this compilation
        if status.get('user_id') != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied to this compilation")

        if status['status'] not in ['running', 'initializing']:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel compilation with status: {status['status']}"
            )

        # Update status to cancelled
        compilation_status[comp_id].update({
            'status': 'cancelled',
            'current_step': 'Compilation cancelled by user',
            'progress': 0,
            'last_updated': datetime.now()
        })

        # Clean up temporary directory if it exists
        temp_dir_str = status.get('temp_dir')
        if temp_dir_str:
            temp_dir = Path(temp_dir_str)
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Error cleaning up temp directory {temp_dir}: {e}")

    # Kill any running processes
    with process_lock:
        # Kill data fetching process if running
        if comp_id in data_fetching_processes:
            process = data_fetching_processes[comp_id]
            try:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                logger.info(f"Successfully terminated data fetching process for {comp_id}")
            except Exception as e:
                logger.error(f"Error terminating data fetching process for {comp_id}: {e}")

    return {"message": "Compilation cancelled successfully"}


@app.get("/download-pdf")
async def download_pdf(
    temp_id: str,
    file_name: str,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Download the generated PDF file. Requires authentication."""
    pdf_path = verify_and_get_file_path(temp_id, current_user, file_name + ".pdf")
    
    return FileResponse(
        path=pdf_path,
        filename=file_name,
        media_type="application/pdf"
    )


@app.get("/download-zip")
async def download_zip(
    temp_id: str,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Download the project ZIP archive. Requires authentication."""
    zip_path = verify_and_get_file_path(temp_id, current_user, "project.zip")
    
    return FileResponse(
        path=zip_path,
        filename="project.zip",
        media_type="application/zip"
    )


# ── Template static assets (public — CSS/images only, no report data) ────────

@app.get("/template-assets/{file_path:path}")
async def serve_template_asset(file_path: str):
    """
    Serve CSS and image assets from the local HTML template directory.
    Public (no auth) — these files contain no report data, only styling.
    Only files inside css/ and assets/ sub-directories are accessible.
    """
    if html_template_path is None:
        raise HTTPException(status_code=404, detail="No local template path configured")

    # Restrict to safe subdirectories
    allowed_prefixes = ("css/", "assets/")
    if not any(file_path.startswith(p) for p in allowed_prefixes):
        raise HTTPException(status_code=403, detail="Access denied")

    # Resolve and validate path stays within the template directory
    template_dir = Path(html_template_path) / "dibiso-html"
    target = (template_dir / file_path).resolve()
    try:
        target.relative_to(template_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Path traversal denied")

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")

    return FileResponse(str(target))


# Health check endpoint (public)
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("DEV_API_HOST"), port=int(os.getenv("DEV_API_PORT")))
