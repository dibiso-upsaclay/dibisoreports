import React, { useState, useEffect, useRef } from 'react';
import { Archive, CheckCircle, Download, FileText, Github, Loader2, XCircle, Lock, LogIn, User, LogOut, Settings, ArrowLeft } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL

// ── i18n ──────────────────────────────────────────────────────────────────────

const TRANSLATIONS = {
  en: {
    appDescription: "Generate the open-science report for a given year and HAL collection.",
    login: "Login",
    welcome: "Welcome,",
    account: "Account",
    adminPanel: "Admin Panel",
    admin: "Admin",
    logout: "Logout",

    loginTitle: "Login",
    error: "Error",
    username: "Username",
    enterUsername: "Enter your username",
    password: "Password",
    enterPassword: "Enter your password",
    cancel: "Cancel",

    accountTitle: "Account",
    profileSaved: "Profile saved successfully.",
    profileDescription: "Optional profile information used to pre-fill reporter details in report forms.",
    firstName: "First name",
    lastName: "Last name",
    email: "Email",
    optional: "Optional",
    saveProfile: "Save profile",
    hidePasswordChange: "Hide password change",
    changePassword: "Change password",
    currentPassword: "Current password",
    newPassword: "New password",
    confirmNewPassword: "Confirm new password",
    changePasswordBtn: "Change password",

    adminPanelTitle: "Admin Control Panel",
    registerNewUser: "Register New User",
    enterUsernameAdmin: "Enter username",
    enterEmail: "Enter email",
    enterPasswordAdmin: "Enter password",
    role: "Role",
    userRole: "User",
    adminRole: "Admin",
    registerUserBtn: "Register User",
    userManagement: "User Management",
    statusHeader: "Status",
    actionsHeader: "Actions",
    active: "Active",
    inactive: "Inactive",
    deactivate: "Deactivate",
    activate: "Activate",
    changePasswordAdmin: "Change Password",
    delete: "Delete",
    promptNewPassword: "Enter new password for this user:",
    confirmDeleteUser: (u) => `Are you sure you want to permanently delete user "${u}"? This action cannot be undone.`,

    reportParameters: "Report Parameters",
    year: "Year",
    yearDescription: "Year for which to make the report.",
    yearPlaceholder: "e.g., 2024",
    halCollectionId: "HAL collection ID",
    halDescription: "The HAL collection ID used to fetch the data.",
    halPlaceholder: "e.g., LABORATOIRE-EXEMPLE",
    labAcronym: "Lab Acronym",
    labAcronymDescription: "The laboratory acronym that will be displayed on the title page.",
    labAcronymPlaceholder: "e.g., LABO",
    labName: "Lab Name",
    labNameDescription: "The laboratory name that will be displayed on the title page.",
    labNamePlaceholder: "e.g., Laboratory Example",
    maxEntities: "Max entities:",
    maxEntitiesDescription: "For maps, limits to the number of DOIs to use for creating the plot. A lower value may skip some collaborating institutions on the map but will significantly decrease the report generation time.",
    reporter: "Lab contact",
    reporterDescription: "Name displayed on the last page of the report. Optional.",
    reporterPlaceholder: "e.g., First Last",
    reporterEmail: "Contact email",
    reporterEmailDescription: "Email address shown on the last page. Optional.",
    reporterEmailPlaceholder: "e.g., firstname.lastname@example.fr",

    starting: "Starting...",
    compiling: "Compiling...",
    generateReport: "Generate Report",
    cancelCompilation: "Cancel Compilation",
    startingGeneration: "Starting the report generation...",
    generatingReport: "Generating the report...",
    processing: "Processing...",

    generationSuccessful: "Generation Successful!",
    partialSuccess: "Partial Success - PDF Compilation Failed",
    finalizingExport: "Finalising export (HTML, CSS, annotations)…",
    goToEditingPage: "Go to the editing page to add or change comments.",
    goToEditingPageBtn: "Go to editing page",
    goodNews: "Good news:",
    partialMessage: "Your data has been successfully fetched and the ZIP archive is available for download. You can download the ZIP archive and open the HTML report in a browser.",

    downloadFiles: "Download Files",
    reportPdf: "Report PDF",
    reportPdfDescription: "Download the compiled report PDF document",
    downloading: "Downloading...",
    reportBtn: "Report",
    bibliographyPdf: "Bibliography PDF",
    bibliographyPdfDescription: "Download the bibliography PDF document",
    bibliographyBtn: "Bibliography",
    exportZip: "Export ZIP",
    available: "Available",
    exportZipDescription: "Generates the final HTML report (with annotations and embedded CSS) and downloads the complete project as a ZIP archive.",
    generating: "Generating…",
    exportZipBtn: "Export ZIP",

    back: "Back",
    editPageTitle: (acronym, year) => `${acronym} ${year} — Complete the report`,
    saveAndBack: "Save and go back",
    reportPreview: "Report preview",
    loadingPreview: "Loading preview…",

    iframeEditorLabel: "✏️ Comment / analysis (Markdown)",
    iframeEditorPlaceholder: "Write your analysis here (Markdown supported)…",
    iframeEditing: "Editing…",
    iframeSaved: "✓ Saved",

    instructionsText: "Currently, you can generate an open-science report from an HAL collection. This web application is used to create the BiSO at the Université Paris-Saclay. BiSO stands for Bilan de la Science Ouverte (open-science report).",
    howItWorks: "How it works:",
    step1: "Fill out the fields with the HAL collection ID, lab name, and lab acronym",
    step2: "Click on the generate button to generate the report. Depending on the size of the collection, you may have to wait a few minutes.",
    step3: "Download the report in PDF format or the ZIP archive containing the HTML report and all figures.",

    validationAllFields: "Please fill in all required fields",
    validationYear: (maxYear) => `Please enter a valid year between 1000 and ${maxYear}`,
    loginFailed: "Login failed",
    fetchUserDataFailed: "Failed to fetch user data",
    passwordChangedSuccess: "Password changed successfully!",
    passwordsMustMatch: "New passwords do not match",
    passwordTooShort: "New password must be at least 6 characters long",
    passwordChangeFailed: "Password change failed",
    userRegisteredSuccess: "User registered successfully!",
    registrationFailed: "Registration failed",
    roleUpdatedSuccess: "User role updated successfully!",
    userDeactivatedSuccess: "User deactivated successfully!",
    userActivatedSuccess: "User activated successfully!",
    userDeletedSuccess: "User deleted successfully!",
    compilationCancelled: "Compilation cancelled",
    exportFailed: (msg) => `Export ZIP failed: ${msg}`,
    pollingFailed: (msg) => `Polling failed: ${msg}`,
    downloadFailed: (type) => `Failed to download ${type.toUpperCase()}`,
  },
  fr: {
    appDescription: "Générez le bilan de science ouverte pour une année et une collection HAL.",
    login: "Se connecter",
    welcome: "Bienvenue,",
    account: "Compte",
    adminPanel: "Panneau d'administration",
    admin: "Admin",
    logout: "Déconnexion",

    loginTitle: "Connexion",
    error: "Erreur",
    username: "Identifiant",
    enterUsername: "Saisissez votre identifiant",
    password: "Mot de passe",
    enterPassword: "Saisissez votre mot de passe",
    cancel: "Annuler",

    accountTitle: "Compte",
    profileSaved: "Profil sauvegardé.",
    profileDescription: "Informations de profil optionnelles pour pré-remplir les champs référent dans les formulaires.",
    firstName: "Prénom",
    lastName: "Nom",
    email: "Email",
    optional: "Optionnel",
    saveProfile: "Sauvegarder le profil",
    hidePasswordChange: "Masquer le changement de mot de passe",
    changePassword: "Changer le mot de passe",
    currentPassword: "Mot de passe actuel",
    newPassword: "Nouveau mot de passe",
    confirmNewPassword: "Confirmer le nouveau mot de passe",
    changePasswordBtn: "Changer le mot de passe",

    adminPanelTitle: "Panneau d'administration",
    registerNewUser: "Créer un compte utilisateur",
    enterUsernameAdmin: "Saisissez l'identifiant",
    enterEmail: "Saisissez l'email",
    enterPasswordAdmin: "Saisissez le mot de passe",
    role: "Rôle",
    userRole: "Utilisateur",
    adminRole: "Administrateur",
    registerUserBtn: "Créer l'utilisateur",
    userManagement: "Gestion des utilisateurs",
    statusHeader: "Statut",
    actionsHeader: "Actions",
    active: "Actif",
    inactive: "Inactif",
    deactivate: "Désactiver",
    activate: "Activer",
    changePasswordAdmin: "Changer le mot de passe",
    delete: "Supprimer",
    promptNewPassword: "Entrez le nouveau mot de passe pour cet utilisateur :",
    confirmDeleteUser: (u) => `Êtes-vous sûr de vouloir supprimer définitivement l'utilisateur « ${u} » ? Cette action est irréversible.`,

    reportParameters: "Paramètres du rapport",
    year: "Année",
    yearDescription: "Année pour laquelle générer le rapport.",
    yearPlaceholder: "ex. 2024",
    halCollectionId: "Identifiant de collection HAL",
    halDescription: "L'identifiant de collection HAL utilisé pour récupérer les données.",
    halPlaceholder: "ex. LABORATOIRE-EXEMPLE",
    labAcronym: "Acronyme du laboratoire",
    labAcronymDescription: "L'acronyme du laboratoire affiché sur la page de titre.",
    labAcronymPlaceholder: "ex. LABO",
    labName: "Nom du laboratoire",
    labNameDescription: "Le nom du laboratoire affiché sur la page de titre.",
    labNamePlaceholder: "ex. Laboratoire Exemple",
    maxEntities: "Max entités :",
    maxEntitiesDescription: "Pour les cartes, limite le nombre de DOIs utilisés pour créer le graphique. Une valeur plus faible peut omettre certains partenaires sur la carte mais réduira significativement le temps de génération.",
    reporter: "Référent·e laboratoire",
    reporterDescription: "Nom affiché sur la dernière page du rapport. Optionnel.",
    reporterPlaceholder: "ex. Prénom Nom",
    reporterEmail: "Email référent·e",
    reporterEmailDescription: "Adresse email affichée sur la dernière page. Optionnel.",
    reporterEmailPlaceholder: "ex. prenom.nom@exemple.fr",

    starting: "Démarrage...",
    compiling: "Génération...",
    generateReport: "Générer le rapport",
    cancelCompilation: "Annuler la génération",
    startingGeneration: "Démarrage de la génération...",
    generatingReport: "Génération du rapport...",
    processing: "Traitement...",

    generationSuccessful: "Génération réussie !",
    partialSuccess: "Succès partiel — Génération du PDF échouée",
    finalizingExport: "Finalisation de l'export en cours (HTML, CSS, annotations)…",
    goToEditingPage: "Accéder à la page d'édition pour ajouter ou modifier des commentaires.",
    goToEditingPageBtn: "Aller à la page d'édition",
    goodNews: "Bonne nouvelle :",
    partialMessage: "Vos données ont été récupérées avec succès et l'archive ZIP est disponible au téléchargement. Vous pouvez télécharger l'archive ZIP et ouvrir le rapport HTML dans un navigateur.",

    downloadFiles: "Téléchargement",
    reportPdf: "Rapport PDF",
    reportPdfDescription: "Télécharger le rapport PDF compilé",
    downloading: "Téléchargement...",
    reportBtn: "Rapport",
    bibliographyPdf: "Bibliographie PDF",
    bibliographyPdfDescription: "Télécharger la bibliographie PDF",
    bibliographyBtn: "Bibliographie",
    exportZip: "Exporter ZIP",
    available: "Disponible",
    exportZipDescription: "Génère le rapport HTML final (avec annotations et CSS embarqué) et télécharge le projet complet en ZIP.",
    generating: "Génération en cours…",
    exportZipBtn: "Exporter ZIP",

    back: "Retour",
    editPageTitle: (acronym, year) => `${acronym} ${year} — Compléter le rapport`,
    saveAndBack: "Sauvegarder et revenir",
    reportPreview: "Aperçu du rapport",
    loadingPreview: "Chargement de l'aperçu…",

    iframeEditorLabel: "✏️ Commentaire / analyse (Markdown)",
    iframeEditorPlaceholder: "Rédigez votre analyse ici (Markdown supporté)…",
    iframeEditing: "Modification…",
    iframeSaved: "✓ Sauvegardé",

    instructionsText: "Vous pouvez générer un bilan de science ouverte à partir d'une collection HAL. Cette application est utilisée pour créer le BiSO à l'Université Paris-Saclay. BiSO signifie Bilan de la Science Ouverte.",
    howItWorks: "Comment ça marche :",
    step1: "Remplissez les champs avec l'identifiant de collection HAL, le nom et l'acronyme du laboratoire.",
    step2: "Cliquez sur le bouton de génération. Selon la taille de la collection, la génération peut prendre quelques minutes.",
    step3: "Téléchargez le rapport en PDF ou l'archive ZIP contenant le rapport HTML et toutes les figures.",

    validationAllFields: "Veuillez remplir tous les champs obligatoires",
    validationYear: (maxYear) => `Veuillez saisir une année valide entre 1000 et ${maxYear}`,
    loginFailed: "Échec de la connexion",
    fetchUserDataFailed: "Échec de la récupération des données utilisateur",
    passwordChangedSuccess: "Mot de passe modifié avec succès !",
    passwordsMustMatch: "Les nouveaux mots de passe ne correspondent pas",
    passwordTooShort: "Le nouveau mot de passe doit comporter au moins 6 caractères",
    passwordChangeFailed: "Échec du changement de mot de passe",
    userRegisteredSuccess: "Utilisateur créé avec succès !",
    registrationFailed: "Échec de l'inscription",
    roleUpdatedSuccess: "Rôle mis à jour avec succès !",
    userDeactivatedSuccess: "Utilisateur désactivé avec succès !",
    userActivatedSuccess: "Utilisateur activé avec succès !",
    userDeletedSuccess: "Utilisateur supprimé avec succès !",
    compilationCancelled: "Génération annulée",
    exportFailed: (msg) => `Export ZIP échoué : ${msg}`,
    pollingFailed: (msg) => `Polling échoué : ${msg}`,
    downloadFailed: (type) => `Échec du téléchargement : ${type.toUpperCase()}`,
  }
};

// ─────────────────────────────────────────────────────────────────────────────

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

  // Language state
  const [lang, setLang] = useState(localStorage.getItem('lang') || 'en');

  // Persist language preference
  useEffect(() => {
    localStorage.setItem('lang', lang);
  }, [lang]);

  // Current translation object
  const tr = TRANSLATIONS[lang];

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
      setAuthError(tr.passwordsMustMatch);
      return;
    }

    if (passwordData.newPassword.length < 6) {
      setAuthError(tr.passwordTooShort);
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
        throw new Error(errorData.detail || tr.passwordChangeFailed);
      }

      alert(tr.passwordChangedSuccess);
      setShowChangePassword(false);
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmNewPassword: ''
      });
    } catch (err) {
      setAuthError(err.message || tr.passwordChangeFailed);
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
      setError(tr.validationAllFields);
      return false;
    }
    const currentYear = new Date().getFullYear();
    const yearNum = parseInt(year);
    if (isNaN(yearNum) || yearNum < 1000 || yearNum > currentYear + 1) {
      setError(tr.validationYear(currentYear + 1));
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
        throw new Error(tr.loginFailed);
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
        throw new Error(tr.fetchUserDataFailed);
      }
    } catch (err) {
      setAuthError(err.message || tr.loginFailed);
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
        throw new Error(errorData.detail || tr.registrationFailed);
      }
      alert(tr.userRegisteredSuccess);
      setNewUser({
        username: '',
        email: '',
        password: '',
        role: 'user'
      });
      fetchUsers();
    } catch (err) {
      setAuthError(err.message || tr.registrationFailed);
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
      alert(tr.roleUpdatedSuccess);
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
      alert(tr.passwordChangedSuccess);
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
      alert(tr.userDeactivatedSuccess);
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
      alert(tr.userActivatedSuccess);
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
      alert(tr.userDeletedSuccess);
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
        setError(tr.compilationCancelled);
      } else {
        setTimeout(() => pollCompilationStatus(compId), 250);
      }
    } catch (err) {
      setPolling(false);
      setError(tr.pollingFailed(err.message));
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

  function buildEditorHtml(rawHtml, currentAnalyses, apiBase, editorTr) {
    // Asset images (logos) can use absolute API URLs — they don't have CORS issues for <img>
    let html = rawHtml
      .replace(/src="assets\//g, `src="${apiBase}/template-assets/assets/`);

    const i18nJson = JSON.stringify({
      label: editorTr.iframeEditorLabel,
      placeholder: editorTr.iframeEditorPlaceholder,
      editing: editorTr.iframeEditing,
      saved: editorTr.iframeSaved,
    });

    const editorScript = `
<script>
(function() {
  var i18n = ${i18nJson};
  var analyses = ${JSON.stringify(currentAnalyses)};

  function buildEditor(sectionId, currentValue) {
    var wrapper = document.createElement('div');
    wrapper.style.cssText = 'margin:18px 0;border:2px dashed #3b82f6;border-radius:6px;padding:14px 16px;background:#eff6ff;';

    var hdr = document.createElement('div');
    hdr.style.cssText = 'display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;';

    var lbl = document.createElement('span');
    lbl.textContent = i18n.label;
    lbl.style.cssText = 'font-size:11px;font-weight:700;color:#1d4ed8;text-transform:uppercase;letter-spacing:.05em;';

    var status = document.createElement('span');
    status.style.cssText = 'font-size:11px;color:#6b7280;';

    hdr.appendChild(lbl);
    hdr.appendChild(status);

    var ta = document.createElement('textarea');
    ta.value = currentValue;
    ta.placeholder = i18n.placeholder;
    ta.style.cssText = 'width:100%;min-height:100px;padding:8px 10px;border:1px solid #93c5fd;border-radius:4px;font-family:ui-monospace,monospace;font-size:13px;line-height:1.6;resize:vertical;box-sizing:border-box;color:#1e293b;background:#fff;';

    var timer;
    ta.addEventListener('input', function() {
      status.textContent = i18n.editing;
      clearTimeout(timer);
      timer = setTimeout(function() {
        window.parent.postMessage({ type: 'save_analysis', sectionId: sectionId, content: ta.value }, '*');
        status.textContent = i18n.saved;
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

        setReportPreviewHtml(buildEditorHtml(html, analyses, API_BASE_URL, tr));
      } catch (_) {
        setReportPreviewHtml(
          '<body style="font-family:sans-serif;padding:2rem;color:#b91c1c"><h2>Report HTML not available.</h2></body>'
        );
      }
    };

    build();
  }, [editMode, compilationId]); // intentionally omit analyses and lang — editors init from snapshot, then self-manage

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
              else if (s.export_status === 'failed') reject(new Error(tr.exportFailed('')));
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
      setError(tr.exportFailed(e.message));
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
      const downloadId = compilationResult.temp_id || compilationId;

      if (type === 'pdf') {
        const fileParam = fileName || 'report';
        url = `${API_BASE_URL}/download-pdf?temp_id=${downloadId}&file_name=${fileParam}`;
        downloadFileName = fileName === 'biblio' ? `${filePrefix}_bibliography.pdf` : `${filePrefix}_report.pdf`;
      } else {
        url = `${API_BASE_URL}/download-zip?temp_id=${downloadId}`;
        downloadFileName = `${filePrefix}_project.zip`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error(tr.downloadFailed(type));
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
      setError(tr.compilationCancelled);
    } catch (err) {
      setError(`Cancellation failed: ${err.message}`);
    }
  };

  // Language toggle button
  const LangToggle = () => (
    <button
      onClick={() => setLang(l => l === 'en' ? 'fr' : 'en')}
      style={{
        background: 'none',
        border: '1px solid #4b5563',
        borderRadius: 4,
        color: '#9ca3af',
        cursor: 'pointer',
        fontSize: 12,
        fontWeight: 700,
        padding: '3px 8px',
        letterSpacing: '.05em',
      }}
      title={lang === 'en' ? 'Passer en français' : 'Switch to English'}
    >
      {lang === 'en' ? 'FR' : 'EN'}
    </button>
  );

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
              <ArrowLeft size={16} /> {tr.back}
            </button>
            <span style={{ color: '#f9fafb', fontWeight: 600, fontSize: 15 }}>
              {tr.editPageTitle(formData.entityAcronym, formData.year)}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <LangToggle />
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
              <ArrowLeft size={14} /> {tr.saveAndBack}
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
              title={tr.reportPreview}
              sandbox="allow-scripts"
            />
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280', fontSize: 15, gap: 10 }}>
              <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} />
              {tr.loadingPreview}
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
              {tr.appDescription}
            </p>
            {/* Authentication Controls */}
            <div className="mt-4 flex justify-center">
              {!isAuthenticated ? (
                <div className="flex items-center gap-3">
                  <LangToggle />
                  <button
                    onClick={() => {
                      setShowLogin(true);
                    }}
                    className="flex items-center justify-center bg-teal-600 hover:bg-teal-700 text-white font-medium py-2 px-4 rounded-md transition duration-300"
                  >
                    <LogIn className="w-4 h-4 mr-2" />
                    {tr.login}
                  </button>
                </div>
              ) : (
                <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4">
                  <div className="flex items-center text-white mb-2 sm:mb-0">
                    <User className="w-5 h-5 mr-2" />
                    <span>{tr.welcome} {currentUser?.username}</span>
                  </div>
                  <div className="flex flex-wrap items-center justify-center gap-2">
                    <LangToggle />
                    <button
                      onClick={() => { setShowAccount(true); setAuthError(null); setProfileSaveSuccess(false); }}
                      className="flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-3 sm:px-4 rounded-md transition duration-300 text-sm"
                    >
                      <User className="w-4 h-4 mr-1 sm:mr-2" />
                      <span>{tr.account}</span>
                    </button>
                    {currentUser?.role === 'admin' && (
                      <button
                        onClick={() => setShowAdminPanel(!showAdminPanel)}
                        className="flex items-center justify-center bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-3 sm:px-4 rounded-md transition duration-300 text-sm"
                      >
                        <Settings className="w-4 h-4 mr-1 sm:mr-2" />
                        <span className="hidden sm:inline">{tr.adminPanel}</span>
                        <span className="sm:hidden">{tr.admin}</span>
                      </button>
                    )}
                    <button
                      onClick={handleLogout}
                      className="flex items-center justify-center bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-3 sm:px-4 rounded-md transition duration-300 text-sm"
                    >
                      <LogOut className="w-4 h-4 mr-1 sm:mr-2" />
                      {tr.logout}
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
                  <h3 className="text-xl font-semibold text-white">{tr.loginTitle}</h3>
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
                      <p className="text-red-700 font-medium">{tr.error}</p>
                    </div>
                    <p className="text-red-600 mt-1">{authError}</p>
                  </div>
                )}
                <form onSubmit={handleLoginSubmit}>
                  <div className="mb-4">
                    <label htmlFor="login-username" className="block text-sm font-medium text-gray-300 mb-2">
                      {tr.username}
                    </label>
                    <input
                      type="text"
                      id="login-username"
                      name="username"
                      value={loginData.username}
                      onChange={handleLoginInputChange}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                      placeholder={tr.enterUsername}
                      required
                    />
                  </div>
                  <div className="mb-4">
                    <label htmlFor="login-password" className="block text-sm font-medium text-gray-300 mb-2">
                      {tr.password}
                    </label>
                    <input
                      type="password"
                      id="login-password"
                      name="password"
                      value={loginData.password}
                      onChange={handleLoginInputChange}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                      placeholder={tr.enterPassword}
                      required
                    />
                  </div>
                  <div className="flex justify-end space-x-4">
                    <button
                      type="button"
                      onClick={() => setShowLogin(false)}
                      className="px-4 py-2 bg-gray-600 rounded-md text-white hover:bg-gray-700"
                    >
                      {tr.cancel}
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-teal-600 rounded-md text-white hover:bg-teal-700"
                    >
                      {tr.login}
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
                  <h3 className="text-xl font-semibold text-white">{tr.accountTitle}</h3>
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
                      <p className="text-red-700 font-medium">{tr.error}</p>
                    </div>
                    <p className="text-red-600 mt-1">{authError}</p>
                  </div>
                )}
                {profileSaveSuccess && (
                  <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-green-700 font-medium">{tr.profileSaved}</p>
                  </div>
                )}
                {/* Profile section */}
                <form onSubmit={handleProfileSave}>
                  <p className="text-gray-400 text-sm mb-3">{tr.profileDescription}</p>
                  <div className="mb-3">
                    <label className="block text-sm font-medium text-gray-300 mb-1">{tr.firstName}</label>
                    <input
                      type="text"
                      value={profileData.firstName}
                      onChange={e => setProfileData(p => ({ ...p, firstName: e.target.value }))}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder={tr.optional}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="block text-sm font-medium text-gray-300 mb-1">{tr.lastName}</label>
                    <input
                      type="text"
                      value={profileData.lastName}
                      onChange={e => setProfileData(p => ({ ...p, lastName: e.target.value }))}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder={tr.optional}
                    />
                  </div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-300 mb-1">{tr.email}</label>
                    <input
                      type="email"
                      value={profileData.email}
                      onChange={e => setProfileData(p => ({ ...p, email: e.target.value }))}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="flex justify-end mb-6">
                    <button type="submit" className="px-4 py-2 bg-blue-600 rounded-md text-white hover:bg-blue-700 text-sm">
                      {tr.saveProfile}
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
                    {showChangePassword ? tr.hidePasswordChange : tr.changePassword}
                  </button>
                  {showChangePassword && (
                    <form onSubmit={handleChangePasswordSubmit}>
                      <div className="mb-3">
                        <label className="block text-sm font-medium text-gray-300 mb-1">{tr.currentPassword}</label>
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
                        <label className="block text-sm font-medium text-gray-300 mb-1">{tr.newPassword}</label>
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
                        <label className="block text-sm font-medium text-gray-300 mb-1">{tr.confirmNewPassword}</label>
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
                          {tr.changePasswordBtn}
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
                  <h3 className="text-xl font-semibold text-white">{tr.adminPanelTitle}</h3>
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
                      <p className="text-red-700 font-medium">{tr.error}</p>
                    </div>
                    <p className="text-red-600 mt-1">{authError}</p>
                  </div>
                )}
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-white mb-4">{tr.registerNewUser}</h4>
                  <form onSubmit={handleRegisterUserSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="new-username" className="block text-sm font-medium text-gray-300 mb-2">
                        {tr.username}
                      </label>
                      <input
                        type="text"
                        id="new-username"
                        name="username"
                        value={newUser.username}
                        onChange={handleNewUserInputChange}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                        placeholder={tr.enterUsernameAdmin}
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="new-email" className="block text-sm font-medium text-gray-300 mb-2">
                        {tr.email}
                      </label>
                      <input
                        type="email"
                        id="new-email"
                        name="email"
                        value={newUser.email}
                        onChange={handleNewUserInputChange}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                        placeholder={tr.enterEmail}
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="new-password" className="block text-sm font-medium text-gray-300 mb-2">
                        {tr.password}
                      </label>
                      <input
                        type="password"
                        id="new-password"
                        name="password"
                        value={newUser.password}
                        onChange={handleNewUserInputChange}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                        placeholder={tr.enterPasswordAdmin}
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="new-role" className="block text-sm font-medium text-gray-300 mb-2">
                        {tr.role}
                      </label>
                      <select
                        id="new-role"
                        name="role"
                        value={newUser.role}
                        onChange={handleNewUserInputChange}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                      >
                        <option value="user">{tr.userRole}</option>
                        <option value="admin">{tr.adminRole}</option>
                      </select>
                    </div>
                    <div className="md:col-span-2 flex justify-end">
                      <button
                        type="submit"
                        className="px-4 py-2 bg-teal-600 rounded-md text-white hover:bg-teal-700"
                      >
                        {tr.registerUserBtn}
                      </button>
                    </div>
                  </form>
                </div>
                <div>
                  <h4 className="text-lg font-semibold text-white mb-4">{tr.userManagement}</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-gray-700 rounded-lg">
                      <thead>
                        <tr className="border-b border-gray-600">
                          <th className="px-4 py-2 text-left text-gray-300">{tr.username}</th>
                          <th className="px-4 py-2 text-left text-gray-300">{tr.email}</th>
                          <th className="px-4 py-2 text-left text-gray-300">{tr.role}</th>
                          <th className="px-4 py-2 text-left text-gray-300">{tr.statusHeader}</th>
                          <th className="px-4 py-2 text-left text-gray-300">{tr.actionsHeader}</th>
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
                                <option value="user">{tr.userRole}</option>
                                <option value="admin">{tr.adminRole}</option>
                              </select>
                            </td>
                            <td className="px-4 py-2 text-white">
                              {user.is_active ? (
                                <span className="bg-green-500 text-white px-2 py-1 rounded">{tr.active}</span>
                              ) : (
                                <span className="bg-red-500 text-white px-2 py-1 rounded">{tr.inactive}</span>
                              )}
                            </td>
                            <td className="px-4 py-2 text-white flex space-x-2">
                              {user.is_active ? (
                                <button
                                  onClick={() => handleDeactivateUser(user.id)}
                                  className="bg-red-600 hover:bg-red-700 px-2 py-1 rounded text-sm"
                                >
                                  {tr.deactivate}
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleActivateUser(user.id)}
                                  className="bg-green-600 hover:bg-green-700 px-2 py-1 rounded text-sm"
                                >
                                  {tr.activate}
                                </button>
                              )}
                              <button
                                onClick={() => {
                                  const newPassword = prompt(tr.promptNewPassword);
                                  if (newPassword) {
                                    handleChangeUserPassword(user.id, newPassword);
                                  }
                                }}
                                className="bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-sm"
                              >
                                {tr.changePasswordAdmin}
                              </button>
                              <button
                                onClick={() => {
                                  if (confirm(tr.confirmDeleteUser(user.username))) {
                                    handleDeleteUser(user.id);
                                  }
                                }}
                                className="bg-red-800 hover:bg-red-900 px-2 py-1 rounded text-sm"
                              >
                                {tr.delete}
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
                {tr.reportParameters}
              </h3>
              <div className="grid md:grid-cols-2 gap-6">
                {/* Year Input */}
                <div>
                  <label htmlFor="year" className="block text-sm font-medium text-gray-300 mb-2">
                    {tr.year} <span className="text-red-400">*</span>
                    <span className="text-gray-500 font-light"> <br/>
                      {tr.yearDescription}
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
                    placeholder={tr.yearPlaceholder}
                  />
                </div>
                {/* Lab ID Input */}
                <div>
                  <label htmlFor="entityId" className="block text-sm font-medium text-gray-300 mb-2">
                    {tr.halCollectionId} <span className="text-red-400">*</span>
                    <span className="text-gray-500 font-light"> <br/>
                      {tr.halDescription}
                    </span>
                  </label>
                  <input
                    type="text"
                    id="entityId"
                    name="entityId"
                    value={formData.entityId}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                    placeholder={tr.halPlaceholder}
                  />
                </div>
                {/* Lab Acronym Input */}
                <div>
                  <label htmlFor="entityAcronym" className="block text-sm font-medium text-gray-300 mb-2">
                    {tr.labAcronym} <span className="text-red-400">*</span>
                    <span className="text-gray-500 font-light"> <br/>
                      {tr.labAcronymDescription}
                    </span>
                  </label>
                  <input
                    type="text"
                    id="entityAcronym"
                    name="entityAcronym"
                    value={formData.entityAcronym}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                    placeholder={tr.labAcronymPlaceholder}
                  />
                </div>
                {/* Lab Name Input */}
                <div>
                  <label htmlFor="entityFullName" className="block text-sm font-medium text-gray-300 mb-2">
                    {tr.labName} <span className="text-red-400">*</span>
                    <span className="text-gray-500 font-light"> <br/>
                      {tr.labNameDescription}
                    </span>
                  </label>
                  <textarea
                    id="entityFullName"
                    name="entityFullName"
                    value={formData.entityFullName}
                    onChange={handleInputChange}
                    rows={3}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-vertical"
                    placeholder={tr.labNamePlaceholder}
                  />
                </div>
                {/* Max entities Input */}
                <div>
                  <label htmlFor="maxEntities" className="block text-sm font-medium text-gray-300 mb-2">
                    {tr.maxEntities} <span className="text-red-400">*</span> <br/>
                    <span className="text-gray-500 font-light">
                      {tr.maxEntitiesDescription}
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
                  />
                </div>
                {/* Reporter name */}
                <div>
                  <label htmlFor="reporter" className="block text-sm font-medium text-gray-300 mb-2">
                    {tr.reporter}
                    <span className="text-gray-500 font-light"> <br/>
                      {tr.reporterDescription}
                    </span>
                  </label>
                  <input
                    type="text"
                    id="reporter"
                    name="reporter"
                    value={formData.reporter}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                    placeholder={tr.reporterPlaceholder}
                  />
                </div>
                {/* Reporter email */}
                <div>
                  <label htmlFor="reporterEmail" className="block text-sm font-medium text-gray-300 mb-2">
                    {tr.reporterEmail}
                    <span className="text-gray-500 font-light"> <br/>
                      {tr.reporterEmailDescription}
                    </span>
                  </label>
                  <input
                    type="email"
                    id="reporterEmail"
                    name="reporterEmail"
                    value={formData.reporterEmail}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                    placeholder={tr.reporterEmailPlaceholder}
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
                    <span>{isCompiling ? tr.starting : tr.compiling}</span>
                  </>
                ) : (
                  <>
                    <FileText className="w-5 h-5" />
                    <span>{tr.generateReport}</span>
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
                  <span>{tr.cancelCompilation}</span>
                </button>
              )}
            </div>
            {/* Loading indicator with progress bar */}
            {(isCompiling || polling) && !compilationResult && !error && (
              <div className="mb-6 p-6 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center mb-4">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-500 mr-2" />
                  <p className="text-blue-700 font-medium">
                    {isCompiling ? tr.startingGeneration : tr.generatingReport}
                  </p>
                </div>
                {compilationStatus && (
                  <div className="space-y-3">
                    {/* Current Step */}
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-blue-600 font-medium">
                        {compilationStatus.current_step || tr.processing}
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
                  <p className="text-red-700 font-medium">{tr.error}</p>
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
                      ? tr.generationSuccessful
                      : tr.partialSuccess}
                  </p>
                </div>
                {compilationResult.status === 'completed' ? (
                  isExporting ? (
                    <div className="mt-1 flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-green-500 flex-shrink-0" />
                      <p className="text-green-600 text-sm">{tr.finalizingExport}</p>
                    </div>
                  ) : (
                    <div className="mt-1 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <p className="text-green-600">{tr.goToEditingPage}</p>
                      <button
                        onClick={() => setEditMode(true)}
                        className="flex-shrink-0 flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-medium py-2 px-4 rounded-md text-sm transition duration-300"
                      >
                        <FileText className="w-4 h-4" />
                        {tr.goToEditingPageBtn}
                      </button>
                    </div>
                  )
                ) : (
                  <>
                    <p className="text-yellow-600">{compilationResult.message}</p>
                    <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded">
                      <p className="text-blue-700 text-sm">
                        <strong>{tr.goodNews}</strong> {tr.partialMessage}
                      </p>
                    </div>
                    <div className="mt-3">
                      <button
                        onClick={() => setEditMode(true)}
                        className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-medium py-2 px-4 rounded-md text-sm transition duration-300"
                      >
                        <FileText className="w-4 h-4" />
                        {tr.goToEditingPageBtn}
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
                  {tr.downloadFiles}
                </h3>
                <div className="grid md:grid-cols-3 gap-4 mb-6">
                  {/* Report PDF Download - Only show if compilation was completed */}
                  {compilationResult.status === 'completed' && (compilationResult.pdf_available !== false) && (
                    <div className="bg-gray-700 p-6 rounded-lg border border-gray-600 flex flex-col">
                      <div className="flex items-center mb-3">
                        <FileText className="w-6 h-6 text-red-500 mr-2" />
                        <h4 className="font-semibold text-white">{tr.reportPdf}</h4>
                      </div>
                      <p className="text-gray-300 mb-4 text-sm flex-grow">
                        {tr.reportPdfDescription}
                      </p>
                      <button
                        onClick={() => handleDownload('pdf', 'report')}
                        disabled={isDownloading.pdf || isExporting}
                        className="w-full bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-medium py-2 px-4 rounded-md transition duration-300 flex items-center justify-center space-x-2 mt-auto"
                      >
                        {isDownloading.pdf ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>{tr.downloading}</span>
                          </>
                        ) : (
                          <>
                            <Download className="w-4 h-4" />
                            <span>{tr.reportBtn}</span>
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
                        <h4 className="font-semibold text-white">{tr.bibliographyPdf}</h4>
                      </div>
                      <p className="text-gray-300 mb-4 text-sm flex-grow">
                        {tr.bibliographyPdfDescription}
                      </p>
                      <button
                        onClick={() => handleDownload('pdf', 'biblio')}
                        disabled={isDownloading.biblio || isExporting}
                        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 px-4 rounded-md transition duration-300 flex items-center justify-center space-x-2 mt-auto"
                      >
                        {isDownloading.biblio ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>{tr.downloading}</span>
                          </>
                        ) : (
                          <>
                            <Download className="w-4 h-4" />
                            <span>{tr.bibliographyBtn}</span>
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
                          {tr.exportZip}
                          {compilationResult.status === 'partial' && (
                            <span className="ml-2 bg-yellow-500 text-yellow-900 px-2 py-1 rounded text-xs font-medium">
                              {tr.available}
                            </span>
                          )}
                        </h4>
                      </div>
                      <p className="text-gray-300 mb-4 text-sm flex-grow">
                        {tr.exportZipDescription}
                      </p>
                      <button
                        onClick={handleExportZip}
                        disabled={isExporting}
                        className="w-full bg-orange-600 hover:bg-orange-700 disabled:bg-orange-400 text-white font-medium py-2 px-4 rounded-md transition duration-300 flex items-center justify-center space-x-2 mt-auto"
                      >
                        {isExporting ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>{tr.generating}</span>
                          </>
                        ) : (
                          <>
                            <Download className="w-4 h-4" />
                            <span>{tr.exportZipBtn}</span>
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
              {tr.instructionsText}
            </p>
            <h3 className="text-xl font-semibold text-white mb-4">{tr.howItWorks}</h3>
            <div className="space-y-3 text-white">
              <div className="flex items-start">
                <div className="bg-teal-700 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5 flex-shrink-0">1</div>
                <p>{tr.step1}</p>
              </div>
              <div className="flex items-start">
                <div className="bg-teal-700 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5 flex-shrink-0">2</div>
                <p>{tr.step2}</p>
              </div>
              <div className="flex items-start">
                <div className="bg-teal-700 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5 flex-shrink-0">3</div>
                <p>{tr.step3}</p>
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
