document.addEventListener('DOMContentLoaded', () => {
    // --- State Variables ---
    let currentLawId = getLawIdFromUrl() || 1;
    let isPlaying = false;
    let isLoadingAudio = false;

    // --- DOM Elements ---
    const appContainer = document.querySelector('.app-container');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const themeToggle = document.getElementById('theme-toggle');
    const moonIcon = themeToggle.querySelector('.moon-icon');
    const sunIcon = themeToggle.querySelector('.sun-icon');
    
    const pageTitle = document.getElementById('page-title');
    const viewLawLabel = document.getElementById('view-law-label');
    const viewLawTitle = document.getElementById('view-law-title');
    const viewLawBody = document.getElementById('view-law-body');
    
    const likeBtn = document.getElementById('like-btn');
    const likesCountEl = document.getElementById('likes-count');
    const shareBtn = document.getElementById('share-btn');
    const audioBtn = document.getElementById('audio-btn');
    const audioBtnText = document.getElementById('audio-btn-text');
    const audioIconContainer = document.getElementById('audio-icon-container');
    const audioPlayer = document.getElementById('tts-audio-player');
    const toast = document.getElementById('toast-notification');

    // --- Theme Management ---
    initializeTheme();

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    });

    function initializeTheme() {
        const storedTheme = localStorage.getItem('theme');
        if (storedTheme) {
            setTheme(storedTheme);
        } else {
            const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            setTheme(systemPrefersDark ? 'dark' : 'light');
        }
    }

    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        if (theme === 'dark') {
            moonIcon.style.display = 'none';
            sunIcon.style.display = 'block';
        } else {
            moonIcon.style.display = 'block';
            sunIcon.style.display = 'none';
        }
    }

    // --- Sidebar Responsiveness & Collapsing ---
    sidebarToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        if (window.innerWidth < 768) {
            appContainer.classList.toggle('sidebar-open');
        } else {
            appContainer.classList.toggle('sidebar-collapsed');
        }
    });

    // Close mobile sidebar when clicking outside or on layout content
    document.addEventListener('click', (e) => {
        if (window.innerWidth < 768 && appContainer.classList.contains('sidebar-open')) {
            const sidebar = document.getElementById('sidebar');
            if (!sidebar.contains(e.target) && e.target !== sidebarToggle) {
                appContainer.classList.remove('sidebar-open');
            }
        }
    });

    // --- AJAX Navigation & Content Loading ---
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const sectionId = parseInt(link.getAttribute('data-id'));
            loadLaw(sectionId);
            
            // On mobile, automatically dismiss the sidebar navigation drawer
            if (window.innerWidth < 768) {
                appContainer.classList.remove('sidebar-open');
            }
        });
    });

    // Handle browser back/forward buttons
    window.addEventListener('popstate', () => {
        const sectionId = getLawIdFromUrl() || 1;
        loadLaw(sectionId, false);
    });

    function getLawIdFromUrl() {
        const params = new URLSearchParams(window.location.search);
        const law = params.get('law');
        return law ? parseInt(law, 10) : null;
    }

    async function loadLaw(lawId, pushState = true) {
        if (isPlaying || isLoadingAudio) {
            stopAudio();
        }

        try {
            const response = await fetch(`/api/sections/${lawId}`);
            if (!response.ok) {
                throw new Error('Section details failed to load.');
            }
            const data = await response.json();
            
            currentLawId = data.id;

            // Update page UI
            viewLawLabel.textContent = data.label;
            
            if (data.title) {
                viewLawTitle.textContent = data.title;
                pageTitle.textContent = `${data.label} - ${data.title} | 48ቱ የሥልጣን ሕጎች`;
            } else {
                viewLawTitle.textContent = 'በቅርብ ቀን (Coming soon)';
                pageTitle.textContent = `${data.label} - በቅርብ ቀን (Coming soon) | 48ቱ የሥልጣን ሕጎች`;
            }

            if (data.body) {
                viewLawBody.innerHTML = `<p>${data.body.replace(/\n\n/g, '</p><p>')}</p>`;
                viewLawBody.classList.remove('coming-soon');
                audioBtn.removeAttribute('disabled');
                audioBtn.setAttribute('title', 'Listen to this law aloud in Amharic');
            } else {
                viewLawBody.innerHTML = 'ይህ ክፍል ገና አልተተረጎመም። በቅርቡ ይደርሳል! (This law has not been translated yet. Coming soon!)';
                viewLawBody.classList.add('coming-soon');
                audioBtn.setAttribute('disabled', 'true');
                audioBtn.setAttribute('title', 'Audio reader unavailable for coming soon sections');
            }

            // Update active sidebar link
            sidebarLinks.forEach(link => {
                const linkId = parseInt(link.getAttribute('data-id'));
                if (linkId === currentLawId) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });

            // Update likes display
            likesCountEl.textContent = data.likes;
            if (data.liked) {
                likeBtn.classList.add('liked');
                likeBtn.setAttribute('title', 'You have liked this law');
            } else {
                likeBtn.classList.remove('liked');
                likeBtn.setAttribute('title', 'Like this law');
            }

            // Push state to browser history
            if (pushState) {
                const newUrl = `/?law=${data.id}`;
                history.pushState({ lawId: data.id }, '', newUrl);
            }

        } catch (error) {
            console.error('Error loading law:', error);
            showToast('የሕግ ይዘት መጫን አልተቻለም (Failed to load content)');
        }
    }

    // --- Likes Action API ---
    likeBtn.addEventListener('click', async () => {
        if (likeBtn.classList.contains('liked')) {
            showToast('ይህንን ሕግ ቀድመው ወድደውታል (You already liked this law)');
            return;
        }

        try {
            const response = await fetch(`/api/sections/${currentLawId}/like`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            if (!response.ok) {
                throw new Error('Failed to post like');
            }
            const data = await response.json();
            
            // Update likes counter
            likesCountEl.textContent = data.likes;
            likeBtn.classList.add('liked');
            likeBtn.setAttribute('title', 'You have liked this law');
            showToast('ሕጉን ወድደውታል! (You liked this law!)');
        } catch (error) {
            console.error('Error liking section:', error);
            showToast('ምርጫ ማዘመን አልተቻለም (Failed to submit like)');
        }
    });

    // --- TTS Audio Playback ---
    audioBtn.addEventListener('click', () => {
        if (isPlaying) {
            stopAudio();
        } else if (!isLoadingAudio) {
            playAudio();
        }
    });

    async function playAudio() {
        isLoadingAudio = true;
        audioBtn.classList.add('playing');
        audioBtnText.textContent = 'በማዘጋጀት ላይ... (Generating...)';
        
        // Show indicator in icon
        audioIconContainer.innerHTML = `
            <svg class="loading-spinner" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="3">
                <circle cx="12" cy="12" r="10" stroke-dasharray="40 10" stroke-linecap="round"></circle>
                <style>
                    .loading-spinner { animation: spin 1s linear infinite; transform-origin: center; }
                    @keyframes spin { 100% { transform: rotate(360deg); } }
                </style>
            </svg>
        `;

        try {
            // Establish the endpoint source
            const audioSrc = `/api/sections/${currentLawId}/audio`;
            
            // Prime browser audio player
            audioPlayer.src = audioSrc;
            
            // Preload and verify availability
            await new Promise((resolve, reject) => {
                audioPlayer.oncanplaythrough = resolve;
                audioPlayer.onerror = (e) => {
                    // Try to extract server error message if response is JSON error
                    reject(new Error('Audio load failed.'));
                };
                audioPlayer.load();
            });

            isLoadingAudio = false;
            isPlaying = true;
            audioBtnText.textContent = 'አቁም (Stop)';
            
            // Update to Stop button SVG
            audioIconContainer.innerHTML = `
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
                </svg>
            `;
            
            await audioPlayer.play();

        } catch (error) {
            console.error('Error starting audio playback:', error);
            stopAudio();
            
            // Check if backend returned service unavailability or authorization failures
            showToast('የንባብ ድምጽ ማመንጨት አልተቻለም (Audio generation failed)');
        }
    }

    function stopAudio() {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        isPlaying = false;
        isLoadingAudio = false;
        
        audioBtn.classList.remove('playing');
        audioBtnText.textContent = 'አድምጥ (Listen)';
        
        // Reset to standard Play Speaker SVG
        audioIconContainer.innerHTML = `
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
            </svg>
        `;
    }

    // Reset buttons when audio finishes playing
    audioPlayer.addEventListener('ended', () => {
        stopAudio();
    });

    // --- Sharing Link Feature ---
    shareBtn.addEventListener('click', () => {
        const shareUrl = `${window.location.origin}/?law=${currentLawId}`;
        
        if (navigator.share) {
            navigator.share({
                title: pageTitle.textContent,
                text: `48ቱ የሥልጣን ሕጎች - Law ${currentLawId}`,
                url: shareUrl
            }).catch(err => {
                copyUrlToClipboard(shareUrl);
            });
        } else {
            copyUrlToClipboard(shareUrl);
        }
    });

    function copyUrlToClipboard(url) {
        navigator.clipboard.writeText(url).then(() => {
            showToast('የማጋሪያ ሊንክ ተገልብጧል! (Link copied to clipboard!)');
        }).catch(err => {
            console.error('Failed to copy share link:', err);
            showToast('ሊንኩን መቅዳት አልተቻለም (Failed to copy link)');
        });
    }

    // --- Toast Controller ---
    let toastTimeout;
    function showToast(message) {
        clearTimeout(toastTimeout);
        toast.textContent = message;
        toast.classList.add('show');
        
        toastTimeout = setTimeout(() => {
            toast.classList.remove('show');
        }, 3500);
    }
});
