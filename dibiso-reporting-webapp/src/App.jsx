import React, { useState, useEffect, useRef } from 'react';
import { Archive, CheckCircle, Download, FileText, Github, Loader2, XCircle, Lock, UserPlus, LogIn, User, LogOut, Settings, ArrowLeft } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL

const ReportGeneratorInterface = () => {
  const [isCompiling, setIsCompiling] = useState(false);
  const [compilationResult, setCompilationResult] = useState(null);
  const [error, setError] = useState(null);
  const [compilationId, setCompilationId] = useState(null);
  const [polling, setPolling] = useState(false);
  const [compilationStatus, setCompilationStatus] = useState(null);
  const [isDownloading, setIsDownloading] = useState({ pdf: false, zip: false, biblio: false });
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [authError, setAuthError] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  // Form state for report generation
  const [formData, setFormData] = useState({
    year: (new Date().getFullYear() - 1).toString(),
    entityAcronym: '',
    entityFullName: '',
    entityId: '',
    maxEntities: 1000,
    reporter: '',
    reporterEmail: ''
  });
  // Form state for login and registration
  const [loginData, setLoginData] = useState({
    username: '',
    password: ''
  });
  const [registerData, setRegisterData] = useState({
    username: '',
    email: '',
    password: ''
  });
  const [showLogin, setShowLogin] = useState(false);
  const [showAccount, setShowAccount] = useState(false);
  const [profileData, setProfileData] = useState({ firstName: '', lastName: '', email: '' });
  const [profileSaveSuccess, setProfileSaveSuccess] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmNewPassword: ''
  });
  // Admin control panel state
  const [showAdminPanel, setShowAdminPanel] = useState(false);
  const [users, setUsers] = useState([]);
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    password: '',
    role: 'user'
  });

  // Edit Report state
  const [editMode, setEditMode] = useState(false);
  const [sections, setSections] = useState([]);
  const [analyses, setAnalyses] = useState({});
  const [isExporting, setIsExporting] = useState(false);

  const [reportPreviewHtml, setReportPreviewHtml] = useState('');
  const iframeRef = useRef(null);

  // Effect to check authentication status when the component mounts
  useEffect(() => {
    const checkAuthStatus = async () => {
      if (token) {
        try {
          const response = await fetch(`${API_BASE_URL}/users/me`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          if (response.ok) {
            const userData = await response.json();
            setIsAuthenticated(true);
            setCurrentUser(userData);
            fetchProfile();
            if (userData.role === 'admin') {
              fetchUsers();
            }
          } else {
            localStorage.removeItem('token');
            setToken(null);
            setIsAuthenticated(false);
            setCurrentUser(null);
          }
        } catch (err) {
          console.error('Error checking authentication status:', err);
          localStorage.removeItem('token');
          setToken(null);
          setIsAuthenticated(false);
          setCurrentUser(null);
        }
      }
    };
    checkAuthStatus();
  }, [token]);

  // Fetch users for admin panel
  const fetchUsers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const usersData = await response.json();
        setUsers(usersData);
      } else {
        throw new Error('Failed to fetch users');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchProfile = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/me/profile`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const profile = await response.json();
        const firstName = profile.first_name || '';
        const lastName = profile.last_name || '';
        const email = profile.email || '';
        setProfileData({ firstName, lastName, email });
        setFormData(prev => ({
          ...prev,
          reporter: prev.reporter || [firstName, lastName].filter(Boolean).join(' '),
          reporterEmail: prev.reporterEmail || email,
        }));
      }
    } catch (err) {
      console.error('Error fetching profile:', err);
    }
  };

  // Update token in localStorage whenever it changes
  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }, [token]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleLoginInputChange = (e) => {
    const { name, value } = e.target;
    setLoginData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleNewUserInputChange = (e) => {
    const { name, value } = e.target;
    setNewUser(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handlePasswordInputChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleChangePasswordSubmit = async (e) => {
    e.preventDefault();
    setAuthError(null);

    if (passwordData.newPassword !== passwordData.confirmNewPassword) {
      setAuthError('New passwords do not match');
      return;
    }

    if (passwordData.newPassword.length < 6) {
      setAuthError('New password must be at least 6 characters long');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/users/me/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          current_password: passwordData.currentPassword,
          new_password: passwordData.newPassword
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to change password');
      }

      alert('Password changed successfully!');
      setShowChangePassword(false);
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmNewPassword: ''
      });
    } catch (err) {
      setAuthError(err.message || 'Password change failed');
    }
  };

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setAuthError(null);
    setProfileSaveSuccess(false);
    try {
      const response = await fetch(`${API_BASE_URL}/users/me/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          first_name: profileData.firstName || null,
          last_name: profileData.lastName || null,
          email: profileData.email || null,
        })
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save profile');
      }
      setProfileSaveSuccess(true);
      const fullName = [profileData.firstName, profileData.lastName].filter(Boolean).join(' ');
      setFormData(prev => ({
        ...prev,
        reporter: fullName,
        reporterEmail: profileData.email || '',
      }));
    } catch (err) {
      setAuthError(err.message || 'Profile save failed');
    }
  };

  const validateForm = () => {
    const { year, entityAcronym, entityFullName, entityId, maxEntities } = formData;
    if (!year || !entityAcronym || !entityFullName || !entityId || !maxEntities) {
      setError('Please fill in all required fields');
      return false;
    }
    const currentYear = new Date().getFullYear();
    const yearNum = parseInt(year);
    if (isNaN(yearNum) || yearNum < 1000 || yearNum > currentYear + 1) {
      setError(`Please enter a valid year between 1000 and ${currentYear + 1}`);
      return false;
    }
    return true;
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setAuthError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
          username: loginData.username,
          password: loginData.password
        })
      });
      if (!response.ok) {
        throw new Error('Login failed');
      }
      const data = await response.json();
      setToken(data.access_token);

      // Fetch user information
      const userResponse = await fetch(`${API_BASE_URL}/users/me`, {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      });
      if (userResponse.ok) {
        const userData = await userResponse.json();
        setCurrentUser(userData);
        setIsAuthenticated(true);
        fetchProfile();
        setShowLogin(false);
      } else {
        throw new Error('Failed to fetch user data');
      }
    } catch (err) {
      setAuthError(err.message || 'Login failed');
    }
  };

  // Fetch users when the relevant state changes
  useEffect(() => {
    if (isAuthenticated && currentUser?.role === 'admin' && token) {
      fetchUsers();
    }
  }, [isAuthenticated, currentUser, token]);

  const handleLogout = () => {
    setToken(null);
    setIsAuthenticated(false);
    setCurrentUser(null);
  };

  const handleRegisterUserSubmit = async (e) => {
    e.preventDefault();
    setAuthError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newUser)
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
      }
      const data = await response.json();
      alert('User registered successfully!');
      setNewUser({
        username: '',
        email: '',
        password: '',
        role: 'user'
      });
      fetchUsers();
    } catch (err) {
      setAuthError(err.message || 'Registration failed');
    }
  };

  const handleChangeUserRole = async (userId, newRole) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          role: newRole
        })
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update user role');
      }
      alert('User role updated successfully!');
      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleChangeUserPassword = async (userId, newPassword) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          new_password: newPassword
        })
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to change password');
      }
      alert('Password changed successfully!');
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeactivateUser = async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/deactivate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to deactivate user');
      }
      alert('User deactivated successfully!');
      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleActivateUser = async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/activate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to activate user');
      }
      alert('User activated successfully!');
      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteUser = async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete user');
      }
      alert('User deleted successfully!');
      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const pollCompilationStatus = async (compId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/compilation-status/${compId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error('Failed to fetch compilation status');
      }
      const status = await response.json();
      setCompilationStatus(status);
      
      if (status.status === 'completed') {
        setPolling(false);
        try {
          const resultResponse = await fetch(`${API_BASE_URL}/compilation-result/${compId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (!resultResponse.ok) throw new Error('Failed to fetch compilation result');
          const result = await resultResponse.json();
          setCompilationResult({ ...result, status: 'completed' });

          // Load sections and existing analyses, then enter edit mode
          try {
            const [secRes, anaRes] = await Promise.all([
              fetch(`${API_BASE_URL}/report-sections/${compId}`, { headers: { 'Authorization': `Bearer ${token}` } }),
              fetch(`${API_BASE_URL}/analyses/${compId}`,         { headers: { 'Authorization': `Bearer ${token}` } }),
            ]);
            if (secRes.ok) setSections(await secRes.json());
            if (anaRes.ok) setAnalyses(await anaRes.json());
            setEditMode(true);
          } catch (e) {
            console.error('Failed to load sections/analyses:', e);
          }
        } catch (err) {
          setError(`Failed to fetch result: ${err.message}`);
        }
        setCompilationStatus(null);
      } else if (status.status === 'partial') {
        setPolling(false);
        // For partial status, try to get the result but handle failure gracefully
        try {
          const resultResponse = await fetch(`${API_BASE_URL}/compilation-result/${compId}`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          if (resultResponse.ok) {
            const result = await resultResponse.json();
            setCompilationResult({ ...result, status: 'partial' });
          } else {
            setCompilationResult({
              status: 'partial',
              message: 'Data fetching completed successfully, but PDF compilation failed or timed out. ZIP archive is available for download.',
              compilation_id: compId,
              zip_available: true,
              pdf_available: false
            });
          }
        } catch (err) {
          setCompilationResult({
            status: 'partial',
            message: 'Data fetching completed successfully, but PDF compilation failed or timed out. ZIP archive is available for download.',
            compilation_id: compId,
            zip_available: true,
            pdf_available: false
          });
        }
        // Figures and data are available even in partial mode — enter edit mode
        try {
          const [secRes, anaRes] = await Promise.all([
            fetch(`${API_BASE_URL}/report-sections/${compId}`, { headers: { 'Authorization': `Bearer ${token}` } }),
            fetch(`${API_BASE_URL}/analyses/${compId}`,         { headers: { 'Authorization': `Bearer ${token}` } }),
          ]);
          if (secRes.ok) setSections(await secRes.json());
          if (anaRes.ok) setAnalyses(await anaRes.json());
          setEditMode(true);
        } catch (e) {
          console.error('Failed to load sections/analyses for partial report:', e);
        }
        setCompilationStatus(null);
      } else if (status.status === 'failed') {
        setPolling(false);
        setError(status.current_step || 'Compilation failed');
        setCompilationStatus(null);
      } else if (status.status === 'cancelled') {
        setPolling(false);
        setCompilationStatus(null);
        setError('Compilation cancelled');
      } else {
        setTimeout(() => pollCompilationStatus(compId), 250);
      }
    } catch (err) {
      setPolling(false);
      setError(`Polling failed: ${err.message}`);
      setCompilationStatus(null);
    }
  };

  const handleGeneration = async () => {
    if (!isAuthenticated) {
      setError('You must be logged in to generate a report');
      return;
    }
    if (!validateForm()) {
      return;
    }
    setIsCompiling(true);
    setError(null);
    setCompilationResult(null);
    setCompilationStatus(null);
    try {
      const response = await fetch(`${API_BASE_URL}/generate-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          year: parseInt(formData.year),
          entity_acronym: formData.entityAcronym,
          entity_full_name: formData.entityFullName,
          entity_id: formData.entityId,
          max_entities: formData.maxEntities,
          reporter: formData.reporter,
          reporter_email: formData.reporterEmail
        })
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Compilation failed');
      }
      const result = await response.json();
      setCompilationId(result.compilation_id);
      setPolling(true);
      pollCompilationStatus(result.compilation_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsCompiling(false);
    }
  };

  // ── Edit Report: build iframe srcdoc with inline editors ─────────────

  function buildEditorHtml(rawHtml, currentAnalyses, apiBase) {
    // Asset images (logos) can use absolute API URLs — they don't have CORS issues for <img>
    let html = rawHtml
      .replace(/src="assets\//g, `src="${apiBase}/template-assets/assets/`);

    const editorScript = `
<script>
(function() {
  var analyses = ${JSON.stringify(currentAnalyses)};

  function buildEditor(sectionId, currentValue) {
    var wrapper = document.createElement('div');
    wrapper.style.cssText = 'margin:18px 0;border:2px dashed #3b82f6;border-radius:6px;padding:14px 16px;background:#eff6ff;';

    var hdr = document.createElement('div');
    hdr.style.cssText = 'display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;';

    var lbl = document.createElement('span');
    lbl.textContent = '✏️ Commentaire / analyse (Markdown)';
    lbl.style.cssText = 'font-size:11px;font-weight:700;color:#1d4ed8;text-transform:uppercase;letter-spacing:.05em;';

    var status = document.createElement('span');
    status.style.cssText = 'font-size:11px;color:#6b7280;';

    hdr.appendChild(lbl);
    hdr.appendChild(status);

    var ta = document.createElement('textarea');
    ta.value = currentValue;
    ta.placeholder = 'Rédigez votre analyse ici (Markdown supporté)…';
    ta.style.cssText = 'width:100%;min-height:100px;padding:8px 10px;border:1px solid #93c5fd;border-radius:4px;font-family:ui-monospace,monospace;font-size:13px;line-height:1.6;resize:vertical;box-sizing:border-box;color:#1e293b;background:#fff;';

    var timer;
    ta.addEventListener('input', function() {
      status.textContent = 'Modification…';
      clearTimeout(timer);
      timer = setTimeout(function() {
        window.parent.postMessage({ type: 'save_analysis', sectionId: sectionId, content: ta.value }, '*');
        status.textContent = '✓ Sauvegardé';
      }, 800);
    });

    wrapper.appendChild(hdr);
    wrapper.appendChild(ta);
    return wrapper;
  }

  document.querySelectorAll('section[id]').forEach(function(section) {
    var sectionId = section.id.replace(/-/g, '_');
    var editor = buildEditor(sectionId, analyses[sectionId] || '');

    var existing = section.querySelector('.analysis');
    if (existing) {
      existing.replaceWith(editor);
    } else {
      var placeholder = section.querySelector('.dibiso-info');
      if (placeholder) placeholder.replaceWith(editor);
      else section.appendChild(editor);
    }
  });
})();
<\/script>`;

    return html.replace('</body>', editorScript + '\n</body>');
  }

  // Fetch report HTML + inline CSS, then build iframe srcdoc
  useEffect(() => {
    if (!editMode || !compilationId) return;
    setReportPreviewHtml('');

    const build = async () => {
      try {
        // Fetch the rendered report HTML (requires auth)
        const htmlRes = await fetch(
          `${API_BASE_URL}/download-html?temp_id=${compilationId}&file_name=report`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        if (!htmlRes.ok) throw new Error('HTML not available');
        let html = await htmlRes.text();

        // Inline CSS: sandboxed iframes treat <link> cross-origin fetches as blocked.
        // Fetch each CSS file from React's origin and embed it as a <style> block.
        const cssFiles = ['biso.css', 'base.css', 'print.css'];
        for (const file of cssFiles) {
          try {
            const cssRes = await fetch(`${API_BASE_URL}/template-assets/css/${file}`);
            if (cssRes.ok) {
              const css = await cssRes.text();
              html = html.replace(
                new RegExp(`<link[^>]+href="css/${file}"[^>]*>`, 'g'),
                `<style>\n${css}\n</style>`
              );
            }
          } catch (_) { /* skip missing CSS */ }
        }

        setReportPreviewHtml(buildEditorHtml(html, analyses, API_BASE_URL));
      } catch (_) {
        setReportPreviewHtml(
          '<body style="font-family:sans-serif;padding:2rem;color:#b91c1c"><h2>Report HTML not available.</h2></body>'
        );
      }
    };

    build();
  }, [editMode, compilationId]); // intentionally omit analyses — editors init from snapshot, then self-manage

  // Listen for save_analysis postMessages from the iframe
  useEffect(() => {
    if (!editMode) return;
    const handler = (event) => {
      if (event.data?.type !== 'save_analysis') return;
      const { sectionId, content } = event.data;
      setAnalyses(prev => ({ ...prev, [sectionId]: content }));
      fetch(`${API_BASE_URL}/analyses/${compilationId}/${sectionId}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      }).catch(err => console.error('Analysis save failed:', err));
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, [editMode, compilationId, token]);

  // Poll export status after leaving edit mode so isExporting clears when done
  useEffect(() => {
    if (!isExporting || editMode || !compilationId) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/compilation-status/${compilationId}`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        const s = await res.json();
        if (s.export_status === 'done' || s.export_status === 'failed') {
          if (!cancelled) setIsExporting(false);
        } else {
          if (!cancelled) setTimeout(poll, 1000);
        }
      } catch {
        if (!cancelled) setIsExporting(false);
      }
    };
    setTimeout(poll, 1000);
    return () => { cancelled = true; };
  }, [isExporting, editMode, compilationId]);

  // ─────────────────────────────────────────────────────────────────────

  const handleExportZip = async () => {
    if (!compilationId) return;
    setIsExporting(true);
    try {
      // Check current export status before triggering a new export
      const statusRes = await fetch(`${API_BASE_URL}/compilation-status/${compilationId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const currentStatus = await statusRes.json();

      if (currentStatus.export_status !== 'done' && currentStatus.export_status !== 'rendering') {
        const res = await fetch(`${API_BASE_URL}/export/${compilationId}`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (!res.ok) throw new Error(await res.text());
      }

      if (currentStatus.export_status !== 'done') {
        await new Promise((resolve, reject) => {
          const poll = async () => {
            try {
              const sr = await fetch(`${API_BASE_URL}/compilation-status/${compilationId}`, {
                headers: { 'Authorization': `Bearer ${token}` },
              });
              const s = await sr.json();
              if (s.export_status === 'done') resolve(s);
              else if (s.export_status === 'failed') reject(new Error("L'export a échoué"));
              else setTimeout(poll, 800);
            } catch (e) { reject(e); }
          };
          setTimeout(poll, 800);
        });
      }

      const downloadId = compilationResult?.temp_id || compilationId;
      const blob = await fetch(`${API_BASE_URL}/download-zip?temp_id=${downloadId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      }).then(r => { if (!r.ok) throw new Error('Download failed'); return r.blob(); });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${formData.year}_${formData.entityAcronym}_export.zip`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      setError(`Export ZIP échoué : ${e.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  const handleDownload = async (type, fileName = null) => {
    if (!compilationResult) return;
    setIsDownloading(prev => ({ ...prev, [type]: true }));
    try {
      let url;
      let downloadFileName;

      const filePrefix = `${formData.year}_${formData.entityAcronym}`;
      const downloadId = compilationResult.temp_id || compilationId; // Fallback to compilationId

      if (type === 'pdf') {
        const fileParam = fileName || 'report';
        url = `${API_BASE_URL}/download-pdf?temp_id=${downloadId}&file_name=${fileParam}`;
        downloadFileName = fileName === 'biblio' ? `${filePrefix}_bibliography.pdf` : `${filePrefix}_report.pdf`;
      } else {
        url = `${API_BASE_URL}/download-zip?temp_id=${downloadId}`;
        downloadFileName = `${filePrefix}_latex_project.zip`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error(`Failed to download ${type.toUpperCase()}`);
      }
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = downloadFileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      setError(`Download failed: ${err.message}`);
    } finally {
      setIsDownloading(prev => ({ ...prev, [type]: false }));
    }
  };

  const handleCancel = async () => {
    if (!compilationId) return;
    try {
      const response = await fetch(`${API_BASE_URL}/cancel-compilation/${compilationId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to cancel compilation');
      }
      setPolling(false);
      setIsCompiling(false);
      setCompilationId(null);
      setCompilationStatus(null);
      setCompilationResult(null);
      setError('Compilation cancelled');
    } catch (err) {
      setError(`Cancellation failed: ${err.message}`);
    }
  };

  // ── Edit Report view — full-page iframe with inline editors ─────────
  if (editMode) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#030712' }}>
        {/* Header bar */}
        <div style={{ flexShrink: 0, background: '#111827', borderBottom: '1px solid #374151', padding: '10px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <button
              onClick={() => { setEditMode(false); setReportPreviewHtml(''); }}
              style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#9ca3af', background: 'none', border: 'none', cursor: 'pointer', fontSize: 14 }}
            >
              <ArrowLeft size={16} /> Back
            </button>
            <span style={{ color: '#f9fafb', fontWeight: 600, fontSize: 15 }}>
              {formData.entityAcronym} {formData.year} — Compléter le rapport
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button
              onClick={() => {
                if (compilationId) {
                  fetch(`${API_BASE_URL}/export/${compilationId}`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` },
                  }).catch(() => {});
                  setIsExporting(true);
                }
                setEditMode(false);
                setReportPreviewHtml('');
              }}
              style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#0d9488', color: '#fff', border: 'none', borderRadius: 6, padding: '6px 16px', fontSize: 13, cursor: 'pointer', fontWeight: 600 }}
            >
              <ArrowLeft size={14} /> Sauvegarder et revenir
            </button>
          </div>
        </div>

        {/* Report iframe — takes remaining height */}
        <div style={{ flex: 1, overflow: 'hidden', background: '#fff' }}>
          {reportPreviewHtml ? (
            <iframe
              ref={iframeRef}
              srcDoc={reportPreviewHtml}
              style={{ width: '100%', height: '100%', border: 'none' }}
              title="Aperçu du rapport"
              sandbox="allow-scripts"
            />
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280', fontSize: 15, gap: 10 }}>
              <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} />
              Chargement de l&apos;aperçu…
            </div>
          )}
        </div>

        <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 to-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-4">
              <span className="absolute mx-auto py-4 flex border w-fit bg-gradient-to-r blur-xl from-teal-500 via-yellow-400 to-rose-700 bg-clip-text text-6xl box-content font-extrabold text-transparent text-center select-none">
                DiBISO Reporting
              </span>
              <h1 className="relative top-0 w-fit h-auto py-4 justify-center flex bg-gradient-to-r items-center from-teal-500 via-yellow-400 to-rose-700 bg-clip-text text-6xl font-extrabold text-transparent text-center select-auto">
                DiBISO Reporting
              </h1>
            </div>
            <p className="text-white text-lg">
              Generate the open-science report for a given year and HAL collection.
            </p>
            {/* Authentication Controls */}
            <div className="mt-4 flex justify-center">
              {!isAuthenticated ? (
                <>
                  <button
                    onClick={() => {
                      setShowLogin(true);
                    }}
                    className="flex items-center justify-center bg-teal-600 hover:bg-teal-700 text-white font-medium py-2 px-4 rounded-md transition duration-300"
                  >
                    <LogIn className="w-4 h-4 mr-2" />
                    Login
                  </button>
                </>
              ) : (
                <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4">
                  <div className="flex items-center text-white mb-2 sm:mb-0">
                    <User className="w-5 h-5 mr-2" />
                    <span>Welcome, {currentUser?.username}</span>
                  </div>
                  <div className="flex flex-wrap items-center justify-center gap-2">
                    <button
                      onClick={() => { setShowAccount(true); setAuthError(null); setProfileSaveSuccess(false); }}
                      className="flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-3 sm:px-4 rounded-md transition duration-300 text-sm"
                    >
                      <User className="w-4 h-4 mr-1 sm:mr-2" />
                      <span className="hidden sm:inline">Account</span>
                      <span className="sm:hidden">Account</span>
                    </button>
                    {currentUser?.role === 'admin' && (
                      <button
                        onClick={() => setShowAdminPanel(!showAdminPanel)}
                        className="flex items-center justify-center bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-3 sm:px-4 rounded-md transition duration-300 text-sm"
                      >
                        <Settings className="w-4 h-4 mr-1 sm:mr-2" />
                        <span className="hidden sm:inline">Admin Panel</span>
                        <span className="sm:hidden">Admin</span>
                      </button>
                    )}
                    <button
                      onClick={handleLogout}
                      className="flex items-center justify-center bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-3 sm:px-4 rounded-md transition duration-300 text-sm"
                    >
                      <LogOut className="w-4 h-4 mr-1 sm:mr-2" />
                      Logout
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
          {/* Login Modal */}
          {showLogin && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
              <div className="bg-gray-800 rounded-lg shadow-lg p-6 w-full max-w-md">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-semibold text-white">Login</h3>
                  <button
                    onClick={() => setShowLogin(false)}
                    className="text-gray-400 hover:text-white"
                  >
                    <XCircle className="w-6 h-6" />
                  </button>
                </div>
                {authError && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center">
                      <XCircle className="w-5 h-5 text-red-500 mr-2" />
                      <p className="text-red-700 font-medium">Error</p>
                    </div>
                    <p className="text-red-600 mt-1">{authError}</p>
                  </div>
                )}
                <form onSubmit={handleLoginSubmit}>
                  <div className="mb-4">
                    <label htmlFor="login-username" className="block text-sm font-medium text-gray-300 mb-2">
                      Username
                    </label>
                    <input
                      type="text"
                      id="login-username"
                      name="username"
                      value={loginData.username}
                      onChange={handleLoginInputChange}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                      placeholder="Enter your username"
                      required
                    />
                  </div>
                  <div className="mb-4">
                    <label htmlFor="login-password" className="block text-sm font-medium text-gray-300 mb-2">
                      Password
                    </label>
                    <input
                      type="password"
                      id="login-password"
                      name="password"
                      value={loginData.password}
                      onChange={handleLoginInputChange}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                      placeholder="Enter your password"
                      required
                    />
                  </div>
                  <div className="flex justify-end space-x-4">
                    <button
                      type="button"
                      onClick={() => setShowLogin(false)}
                      className="px-4 py-2 bg-gray-600 rounded-md text-white hover:bg-gray-700"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-teal-600 rounded-md text-white hover:bg-teal-700"
                    >
                      Login
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
          {/* Account Modal */}
          {showAccount && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
              <div className="bg-gray-800 rounded-lg shadow-lg p-6 w-full max-w-md max-h-screen overflow-y-auto">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-semibold text-white">Account</h3>
                  <button
                    onClick={() => { setShowAccount(false); setAuthError(null); setProfileSaveSuccess(false); setShowChangePassword(false); }}
                    className="text-gray-400 hover:text-white"
                  >
                    <XCircle className="w-6 h-6" />
                  </button>
                </div>
                {authError && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center">
                      <XCircle className="w-5 h-5 text-red-500 mr-2" />
                      <p className="text-red-700 font-medium">Error</p>
                    </div>
                    <p className="text-red-600 mt-1">{authError}</p>
                  </div>
                )}
                {profileSaveSuccess && (
                  <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-green-700 font-medium">Profile saved successfully.</p>
                  </div>
                )}
                {/* Profile section */}
                <form onSubmit={handleProfileSave}>
                  <p className="text-gray-400 text-sm mb-3">Optional profile information used to pre-fill reporter details in report forms.</p>
                  <div className="mb-3">
                    <label className="block text-sm font-medium text-gray-300 mb-1">First name</label>
                    <input
                      type="text"
                      value={profileData.firstName}
                      onChange={e => setProfileData(p => ({ ...p, firstName: e.target.value }))}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Optional"
                    />
                  </div>
                  <div className="mb-3">
                    <label className="block text-sm font-medium text-gray-300 mb-1">Last name</label>
                    <input
                      type="text"
                      value={profileData.lastName}
                      onChange={e => setProfileData(p => ({ ...p, lastName: e.target.value }))}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Optional"
                    />
                  </div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
                    <input
                      type="email"
                      value={profileData.email}
                      onChange={e => setProfileData(p => ({ ...p, email: e.target.value }))}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="flex justify-end mb-6">
                    <button type="submit" className="px-4 py-2 bg-blue-600 rounded-md text-white hover:bg-blue-700 text-sm">
                      Save profile
                    </button>
                  </div>
                </form>
                {/* Password change section */}
                <div className="border-t border-gray-600 pt-4">
                  <button
                    type="button"
                    onClick={() => { setShowChangePassword(v => !v); setAuthError(null); }}
                    className="text-sm text-gray-300 hover:text-white flex items-center gap-1 mb-3"
                  >
                    <Lock className="w-4 h-4" />
                    {showChangePassword ? 'Hide password change' : 'Change password'}
                  </button>
                  {showChangePassword && (
                    <form onSubmit={handleChangePasswordSubmit}>
                      <div className="mb-3">
                        <label className="block text-sm font-medium text-gray-300 mb-1">Current password</label>
                        <input
                          type="password"
                          name="currentPassword"
                          value={passwordData.currentPassword}
                          onChange={handlePasswordInputChange}
                          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          required
                        />
                      </div>
                      <div className="mb-3">
                        <label className="block text-sm font-medium text-gray-300 mb-1">New password</label>
                        <input
                          type="password"
                          name="newPassword"
                          value={passwordData.newPassword}
                          onChange={handlePasswordInputChange}
                          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          required
                          minLength="6"
                        />
                      </div>
                      <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-300 mb-1">Confirm new password</label>
                        <input
                          type="password"
                          name="confirmNewPassword"
                          value={passwordData.confirmNewPassword}
                          onChange={handlePasswordInputChange}
                          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          required
                          minLength="6"
                        />
                      </div>
                      <div className="flex justify-end">
                        <button type="submit" className="px-4 py-2 bg-blue-600 rounded-md text-white hover:bg-blue-700 text-sm">
                          Change password
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              </div>
            </div>
          )}
          {/* Admin Control Panel Modal */}
          {showAdminPanel && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
              <div className="bg-gray-800 rounded-lg shadow-lg p-6 w-full max-w-4xl max-h-screen overflow-y-auto">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-semibold text-white">Admin Control Panel</h3>
                  <button
                    onClick={() => setShowAdminPanel(false)}
                    className="text-gray-400 hover:text-white"
                  >
                    <XCircle className="w-6 h-6" />
                  </button>
                </div>
                {authError && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center">
                      <XCircle className="w-5 h-5 text-red-500 mr-2" />
                      <p className="text-red-700 font-medium">Error</p>
                    </div>
                    <p className="text-red-600 mt-1">{authError}</p>
                  </div>
                )}
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-white mb-4">Register New User</h4>
                  <form onSubmit={handleRegisterUserSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="new-username" className="block text-sm font-medium text-gray-300 mb-2">
                        Username
                      </label>
                      <input
                        type="text"
                        id="new-username"
                        name="username"
                        value={newUser.username}
                        onChange={handleNewUserInputChange}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                        placeholder="Enter username"
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="new-email" className="block text-sm font-medium text-gray-300 mb-2">
                        Email
                      </label>
                      <input
                        type="email"
                        id="new-email"
                        name="email"
                        value={newUser.email}
                        onChange={handleNewUserInputChange}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                        placeholder="Enter email"
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="new-password" className="block text-sm font-medium text-gray-300 mb-2">
                        Password
                      </label>
                      <input
                        type="password"
                        id="new-password"
                        name="password"
                        value={newUser.password}
                        onChange={handleNewUserInputChange}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                        placeholder="Enter password"
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="new-role" className="block text-sm font-medium text-gray-300 mb-2">
                        Role
                      </label>
                      <select
                        id="new-role"
                        name="role"
                        value={newUser.role}
                        onChange={handleNewUserInputChange}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                      >
                        <option value="user">User</option>
                        <option value="admin">Admin</option>
                      </select>
                    </div>
                    <div className="md:col-span-2 flex justify-end">
                      <button
                        type="submit"
                        className="px-4 py-2 bg-teal-600 rounded-md text-white hover:bg-teal-700"
                      >
                        Register User
                      </button>
                    </div>
                  </form>
                </div>
                <div>
                  <h4 className="text-lg font-semibold text-white mb-4">User Management</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-gray-700 rounded-lg">
                      <thead>
                        <tr className="border-b border-gray-600">
                          <th className="px-4 py-2 text-left text-gray-300">Username</th>
                          <th className="px-4 py-2 text-left text-gray-300">Email</th>
                          <th className="px-4 py-2 text-left text-gray-300">Role</th>
                          <th className="px-4 py-2 text-left text-gray-300">Status</th>
                          <th className="px-4 py-2 text-left text-gray-300">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {users.map(user => (
                          <tr key={user.id} className="border-b border-gray-600">
                            <td className="px-4 py-2 text-white">{user.username}</td>
                            <td className="px-4 py-2 text-white">{user.email}</td>
                            <td className="px-4 py-2 text-white">
                              <select
                                value={user.role}
                                onChange={(e) => handleChangeUserRole(user.id, e.target.value)}
                                className="px-2 py-1 bg-gray-600 rounded text-white"
                              >
                                <option value="user">User</option>
                                <option value="admin">Admin</option>
                              </select>
                            </td>
                            <td className="px-4 py-2 text-white">
                              {user.is_active ? (
                                <span className="bg-green-500 text-white px-2 py-1 rounded">Active</span>
                              ) : (
                                <span className="bg-red-500 text-white px-2 py-1 rounded">Inactive</span>
                              )}
                            </td>
                            <td className="px-4 py-2 text-white flex space-x-2">
                              {user.is_active ? (
                                <button
                                  onClick={() => handleDeactivateUser(user.id)}
                                  className="bg-red-600 hover:bg-red-700 px-2 py-1 rounded text-sm"
                                >
                                  Deactivate
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleActivateUser(user.id)}
                                  className="bg-green-600 hover:bg-green-700 px-2 py-1 rounded text-sm"
                                >
                                  Activate
                                </button>
                              )}
                              <button
                                onClick={() => {
                                  const newPassword = prompt('Enter new password for this user:');
                                  if (newPassword) {
                                    handleChangeUserPassword(user.id, newPassword);
                                  }
                                }}
                                className="bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-sm"
                              >
                                Change Password
                              </button>
                              <button
                                onClick={() => {
                                  if (confirm(`Are you sure you want to permanently delete user "${user.username}"? This action cannot be undone.`)) {
                                    handleDeleteUser(user.id);
                                  }
                                }}
                                className="bg-red-800 hover:bg-red-900 px-2 py-1 rounded text-sm"
                              >
                                Delete
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}
          {/* Main Card */}
          <div className="bg-gray-800 rounded-xl shadow-lg p-8">
            {/* Input Form */}
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-white mb-6 text-center">
                Report Parameters
              </h3>
              <div className="grid md:grid-cols-2 gap-6">
                {/* Year Input */}
                <div>
                  <label htmlFor="year" className="block text-sm font-medium text-gray-300 mb-2">
                    Year <span className="text-red-400">*</span>
                    <span className="text-gray-500 font-light"> <br/>
                      Year for which to make the report.
                    </span>
                  </label>
                  <input
                    type="number"
                    id="year"
                    name="year"
                    value={formData.year}
                    onChange={handleInputChange}
                    min="1000"
                    max={new Date().getFullYear() + 1}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                    placeholder="e.g., 2024"
                  />
                </div>
                {/* Lab ID Input */}
                <div>
                  <label htmlFor="entityId" className="block text-sm font-medium text-gray-300 mb-2">
                    HAL collection ID <span className="text-red-400">*</span>
                    <span className="text-gray-500 font-light"> <br/>
                      The HAL collection ID used to fetch the data.
                    </span>
                  </label>
                  <input
                    type="text"
                    id="entityId"
                    name="entityId"
                    value={formData.entityId}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                    placeholder="e.g., LABORATOIRE-EXEMPLE"
                  />
                </div>
                {/* Lab Acronym Input */}
                <div>
                  <label htmlFor="entityAcronym" className="block text-sm font-medium text-gray-300 mb-2">
                    Lab Acronym <span className="text-red-400">*</span>
                    <span className="text-gray-500 font-light"> <br/>
                      The laboratory acronym that will be displayed on the title page.
                    </span>
                  </label>
                  <input
                    type="text"
                    id="entityAcronym"
                    name="entityAcronym"
                    value={formData.entityAcronym}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                    placeholder="e.g., LABO"
                  />
                </div>
                {/* Lab Name Input */}
                <div>
                  <label htmlFor="entityFullName" className="block text-sm font-medium text-gray-300 mb-2">
                    Lab Name <span className="text-red-400">*</span>
                    <span className="text-gray-500 font-light"> <br/>
                      The laboratory name that will be displayed on the title page.
                    </span>
                  </label>
                  <textarea
                    id="entityFullName"
                    name="entityFullName"
                    value={formData.entityFullName}
                    onChange={handleInputChange}
                    rows={3}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-vertical"
                    placeholder="e.g., Laboratory Example"
                  />
                </div>
                {/* Max entities Input */}
                <div>
                  <label htmlFor="maxEntities" className="block text-sm font-medium text-gray-300 mb-2">
                    Max entities: <span className="text-red-400">*</span> <br/>
                    <span className="text-gray-500 font-light">
                      For maps, limits to the number of DOIs to use for creating the plot.
                      A lower value may skip some collaborating institutions on the map but will significantly decrease the report generation time.
                    </span>
                  </label>
                  <input
                    type="number"
                    id="maxEntities"
                    name="maxEntities"
                    value={formData.maxEntities}
                    min="1"
                    max="10000"
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                    placeholder="e.g., LABO"
                  />
                </div>
                {/* Reporter name */}
                <div>
                  <label htmlFor="reporter" className="block text-sm font-medium text-gray-300 mb-2">
                    Référent·e laboratoire
                    <span className="text-gray-500 font-light"> <br/>
                      Nom affiché sur la dernière page du rapport. Optionnel.
                    </span>
                  </label>
                  <input
                    type="text"
                    id="reporter"
                    name="reporter"
                    value={formData.reporter}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                    placeholder="e.g., Prénom Nom"
                  />
                </div>
                {/* Reporter email */}
                <div>
                  <label htmlFor="reporterEmail" className="block text-sm font-medium text-gray-300 mb-2">
                    Email référent·e
                    <span className="text-gray-500 font-light"> <br/>
                      Adresse email affichée sur la dernière page. Optionnel.
                    </span>
                  </label>
                  <input
                    type="email"
                    id="reporterEmail"
                    name="reporterEmail"
                    value={formData.reporterEmail}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                    placeholder="e.g., prenom.nom@exemple.fr"
                  />
                </div>
              </div>
            </div>
            {/* Compilation Section */}
            <div className="text-center mb-8">
              <button
                onClick={handleGeneration}
                disabled={isCompiling || polling || !isAuthenticated || isExporting}
                className="bg-teal-700 hover:bg-teal-800 disabled:bg-gray-600 disabled:cursor-not-allowed disabled:opacity-60 text-white font-semibold py-3 px-8 rounded-lg transition duration-300 flex items-center justify-center mx-auto space-x-2 shadow-md"
              >
                {isCompiling || polling ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>{isCompiling ? 'Starting...' : 'Compiling...'}</span>
                  </>
                ) : (
                  <>
                    <FileText className="w-5 h-5" />
                    <span>Generate Report</span>
                  </>
                )}
              </button>
              {polling && (
                <button
                  onClick={handleCancel}
                  className="mt-4 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-semibold py-3 px-8 rounded-lg transition duration-300 flex items-center justify-center mx-auto space-x-2 shadow-md"
                  disabled={!compilationId}
                >
                  <XCircle className="w-5 h-5" />
                  <span>Cancel Compilation</span>
                </button>
              )}
            </div>
            {/* Loading indicator with progress bar */}
            {(isCompiling || polling) && !compilationResult && !error && (
              <div className="mb-6 p-6 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center mb-4">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-500 mr-2" />
                  <p className="text-blue-700 font-medium">
                    {isCompiling ? 'Starting the report generation...' : 'Generating the report...'}
                  </p>
                </div>
                {compilationStatus && (
                  <div className="space-y-3">
                    {/* Current Step */}
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-blue-600 font-medium">
                        {compilationStatus.current_step || 'Processing...'}
                      </span>
                      <span className="text-blue-500">
                        {compilationStatus.progress}%
                      </span>
                    </div>
                    {/* Progress Bar */}
                    <div className="w-full bg-blue-200 rounded-full h-2.5">
                      <div
                        className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-out"
                        style={{ width: `${compilationStatus.progress || 0}%` }}
                      ></div>
                    </div>
                  </div>
                )}
            </div>
            )}
            {/* Status Messages */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center">
                  <XCircle className="w-5 h-5 text-red-500 mr-2" />
                  <p className="text-red-700 font-medium">Error</p>
                </div>
                <p className="text-red-600 mt-1">{error}</p>
              </div>
            )}
            {/* Success Message */}
            {compilationResult && (
              <div className={`mb-6 p-4 border rounded-lg ${
                compilationResult.status === 'completed' 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-yellow-50 border-yellow-200'
              }`}>
                <div className="flex items-center mb-2">
                  {compilationResult.status === 'completed' ? (
                    <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                  ) : (
                    <XCircle className="w-5 h-5 text-yellow-500 mr-2" />
                  )}
                  <p className={`font-medium ${
                    compilationResult.status === 'completed' 
                      ? 'text-green-700' 
                      : 'text-yellow-700'
                  }`}>
                    {compilationResult.status === 'completed' 
                      ? 'Generation Successful!' 
                      : 'Partial Success - PDF Compilation Failed'}
                  </p>
                </div>
                {compilationResult.status === 'completed' ? (
                  isExporting ? (
                    <div className="mt-1 flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-green-500 flex-shrink-0" />
                      <p className="text-green-600 text-sm">Finalisation de l'export en cours (HTML, CSS, annotations)…</p>
                    </div>
                  ) : (
                    <div className="mt-1 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <p className="text-green-600">Go to the editing page to add or change comments.</p>
                      <button
                        onClick={() => setEditMode(true)}
                        className="flex-shrink-0 flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-medium py-2 px-4 rounded-md text-sm transition duration-300"
                      >
                        <FileText className="w-4 h-4" />
                        Go to editing page
                      </button>
                    </div>
                  )
                ) : (
                  <>
                    <p className="text-yellow-600">{compilationResult.message}</p>
                    <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded">
                      <p className="text-blue-700 text-sm">
                        <strong>Good news:</strong> Your data has been successfully fetched and the ZIP archive is available for download.
                        You can download the ZIP file and compile the LaTeX project locally if needed.
                      </p>
                    </div>
                    <div className="mt-3">
                      <button
                        onClick={() => setEditMode(true)}
                        className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-medium py-2 px-4 rounded-md text-sm transition duration-300"
                      >
                        <FileText className="w-4 h-4" />
                        Go to editing page
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}
            {/* Download Section */}
            {compilationResult && (
              <div className="border-t border-gray-600 pt-6">
                <h3 className="text-xl font-semibold text-white mb-4 text-center">
                  Download Files
                </h3>
                <div className="grid md:grid-cols-3 gap-4 mb-6">
                  {/* Report PDF Download - Only show if compilation was completed */}
                  {compilationResult.status === 'completed' && (compilationResult.pdf_available !== false) && (
                    <div className="bg-gray-700 p-6 rounded-lg border border-gray-600 flex flex-col">
                      <div className="flex items-center mb-3">
                        <FileText className="w-6 h-6 text-red-500 mr-2" />
                        <h4 className="font-semibold text-white">Report PDF</h4>
                      </div>
                      <p className="text-gray-300 mb-4 text-sm flex-grow">
                        Download the compiled report PDF document
                      </p>
                      <button
                        onClick={() => handleDownload('pdf', 'report')}
                        disabled={isDownloading.pdf || isExporting}
                        className="w-full bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-medium py-2 px-4 rounded-md transition duration-300 flex items-center justify-center space-x-2 mt-auto"
                      >
                        {isDownloading.pdf ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Downloading...</span>
                          </>
                        ) : (
                          <>
                            <Download className="w-4 h-4" />
                            <span>Report</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}

                  {/* Bibliography PDF Download - Only show if compilation was completed */}
                  {compilationResult.status === 'completed' && (compilationResult.pdf_available !== false) && (
                    <div className="bg-gray-700 p-6 rounded-lg border border-gray-600 flex flex-col">
                      <div className="flex items-center mb-3">
                        <FileText className="w-6 h-6 text-blue-500 mr-2" />
                        <h4 className="font-semibold text-white">Bibliography PDF</h4>
                      </div>
                      <p className="text-gray-300 mb-4 text-sm flex-grow">
                        Download the bibliography PDF document
                      </p>
                      <button
                        onClick={() => handleDownload('pdf', 'biblio')}
                        disabled={isDownloading.biblio || isExporting}
                        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 px-4 rounded-md transition duration-300 flex items-center justify-center space-x-2 mt-auto"
                      >
                        {isDownloading.biblio ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Downloading...</span>
                          </>
                        ) : (
                          <>
                            <Download className="w-4 h-4" />
                            <span>Bibliography</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}

                  {/* ZIP Export — re-renders HTML with annotations + inlined CSS, then downloads ZIP */}
                  {(compilationResult.zip_available !== false) && (
                    <div className={`bg-gray-700 p-6 rounded-lg border border-gray-600 flex flex-col ${
                      compilationResult.status === 'partial' ? 'md:col-span-3' : ''
                    }`}>
                      <div className="flex items-center mb-3">
                        <Archive className="w-6 h-6 text-orange-500 mr-2" />
                        <h4 className="font-semibold text-white">
                          Export ZIP
                          {compilationResult.status === 'partial' && (
                            <span className="ml-2 bg-yellow-500 text-yellow-900 px-2 py-1 rounded text-xs font-medium">
                              Available
                            </span>
                          )}
                        </h4>
                      </div>
                      <p className="text-gray-300 mb-4 text-sm flex-grow">
                        Génère le rapport HTML final (avec annotations et CSS embarqué) et télécharge le projet complet en ZIP.
                      </p>
                      <button
                        onClick={handleExportZip}
                        disabled={isExporting}
                        className="w-full bg-orange-600 hover:bg-orange-700 disabled:bg-orange-400 text-white font-medium py-2 px-4 rounded-md transition duration-300 flex items-center justify-center space-x-2 mt-auto"
                      >
                        {isExporting ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Génération en cours…</span>
                          </>
                        ) : (
                          <>
                            <Download className="w-4 h-4" />
                            <span>Exporter ZIP</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          {/* Instructions */}
          <div className="mt-8 bg-gray-800 rounded-xl shadow-lg p-6">
            <p className="text-white mb-4">
              Currently, you can generate an open-science report from an HAL collection.
              This web application is used to create the BiSO at the Université Paris-Saclay.
              BiSO stands for Bilan de la Science Ouverte (open-science report).
            </p>
            <h3 className="text-xl font-semibold text-white mb-4">How it works:</h3>
            <div className="space-y-3 text-white">
              <div className="flex items-start">
                <div className="bg-teal-700 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5 flex-shrink-0">1</div>
                <p>Fill out the fields with the HAL collection ID, lab name, and lab acronym</p>
              </div>
              <div className="flex items-start">
                <div className="bg-teal-700 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5 flex-shrink-0">2</div>
                <p>Click on the generate button to generate the report. Depending on the size of the collection, you may have to wait a few minutes.</p>
              </div>
              <div className="flex items-start">
                <div className="bg-teal-700 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5 flex-shrink-0">3</div>
                <p>Download the report in PDF or the ZIP archive containing the full report ready to be opened in a LaTeX editor for further editing.</p>
              </div>
            </div>
          </div>
          {/* Footer */}
          <div className="relative flex items-center justify-center mt-8 px-4">
            <p className="text-gray-400 text-sm text-center flex-1">
              <a
                href="https://www.bibliotheques.universite-paris-saclay.fr/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-gray-500"
              >
                DiBISO - Université Paris-Saclay
              </a>
            </p>
            <a
              href="https://github.com/dibiso-upsaclay/dibiso-reporting-webapp"
              target="_blank"
              rel="noopener noreferrer"
              className="absolute right-4 text-sm text-gray-400 hover:text-gray-500 flex items-center"
            >
              <Github className="w-5 h-5 mr-1" />
              <span>GitHub</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  return <ReportGeneratorInterface />;
}

export default App;
