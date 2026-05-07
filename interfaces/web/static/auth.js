// Auth helper — Firebase token management + fetch override
(function() {
    // Pages that don't require auth
    const PUBLIC_PATHS = ['/login', '/static/login.html', '/', '/static/index.html'];
    const currentPath = window.location.pathname;
    const isPublicPage = PUBLIC_PATHS.some(p => currentPath === p || currentPath === p + '/');

    // If on login page, skip all auth logic
    if (currentPath.includes('/login') || currentPath === '/static/login.html') return;

    // If on landing page, don't redirect — just expose helpers
    if (currentPath === '/' || currentPath === '/static/index.html') {
        window.isAuthenticated = () => !!localStorage.getItem('auth_token');
        return;
    }

    // Protected page — require token
    const token = localStorage.getItem('auth_token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // ── Token Refresh ──
    // Load Firebase SDK dynamically for silent token refresh
    function loadFirebaseAndRefresh() {
        if (window._firebaseRefreshLoaded) return;
        window._firebaseRefreshLoaded = true;

        const script1 = document.createElement('script');
        script1.src = 'https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js';
        script1.onload = () => {
            const script2 = document.createElement('script');
            script2.src = 'https://www.gstatic.com/firebasejs/10.12.0/firebase-auth-compat.js';
            script2.onload = () => {
                if (!firebase.apps.length) {
                    firebase.initializeApp({
                        apiKey: "AIzaSyDzXLevCIrkpKbszlWOC4y-V2MiulkAHLA",
                        authDomain: "ai-canvas-5e5cf.firebaseapp.com",
                        projectId: "ai-canvas-5e5cf",
                    });
                }
                // Refresh token every 50 minutes (tokens expire at 60 min)
                setInterval(async () => {
                    const user = firebase.auth().currentUser;
                    if (user) {
                        try {
                            const newToken = await user.getIdToken(true);
                            localStorage.setItem('auth_token', newToken);
                        } catch (e) {
                            console.warn('Token refresh failed:', e);
                        }
                    }
                }, 50 * 60 * 1000);

                // Also refresh once on page load
                firebase.auth().onAuthStateChanged(async (user) => {
                    if (user) {
                        try {
                            const newToken = await user.getIdToken(true);
                            localStorage.setItem('auth_token', newToken);
                        } catch (e) { /* ignore */ }
                    }
                });
            };
            document.head.appendChild(script2);
        };
        document.head.appendChild(script1);
    }
    loadFirebaseAndRefresh();

    // ── Fetch Override — inject Authorization header ──
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        const token = localStorage.getItem('auth_token');
        if (token && typeof url === 'string' && url.startsWith('/api/') && !url.includes('/api/health')) {
            if (!options.headers) options.headers = {};
            if (options.headers instanceof Headers) {
                options.headers.set('Authorization', 'Bearer ' + token);
            } else {
                options.headers['Authorization'] = 'Bearer ' + token;
            }
        }
        return originalFetch(url, options).then(response => {
            if (response.status === 401 || response.status === 403) {
                localStorage.removeItem('auth_token');
                localStorage.removeItem('auth_user');
                localStorage.removeItem('auth_photo');
                window.location.href = '/login';
            }
            return response;
        });
    };

    // ── Logout — also signs out of Firebase ──
    window.logout = function() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        localStorage.removeItem('auth_photo');
        // Sign out of Firebase if loaded
        if (typeof firebase !== 'undefined' && firebase.auth) {
            firebase.auth().signOut().catch(() => {});
        }
        window.location.href = '/login';
    };

    // ── User Info ──
    window.getAuthUser = function() {
        return {
            name: localStorage.getItem('auth_user') || 'User',
            photo: localStorage.getItem('auth_photo') || '',
        };
    };
})();