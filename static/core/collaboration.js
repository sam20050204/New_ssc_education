(function () {
    function getCsrfToken() {
        const tokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return tokenInput ? tokenInput.value : '';
    }

    async function apiFetch(url, options) {
        const response = await fetch(url, options);
        const data = await response.json();
        if (!response.ok || data.success === false) {
            throw new Error(data.error || 'Request failed');
        }
        return data;
    }

    function updateBadge(selector, count) {
        const badge = document.querySelector(selector);
        if (!badge) return;
        badge.textContent = count;
        badge.classList.toggle('hidden', !count);
    }

    function renderNotifications(items, unreadCount) {
        const list = document.querySelector('[data-notification-list]');
        const summary = document.querySelector('[data-notification-summary]');
        if (summary) {
            summary.textContent = `${unreadCount} unread`;
        }
        updateBadge('[data-notification-badge]', unreadCount);
        if (!list) return;
        list.innerHTML = items.length ? items.map(item => `
            <div class="collaboration-item ${item.is_read ? '' : 'is-unread'}" data-notification-item data-notification-id="${item.id}">
                <div class="collaboration-item-main">
                    <div class="priority-dot priority-${item.priority}"></div>
                    <div>
                        <strong>${item.title}</strong>
                        <p>${item.message}</p>
                        <small>${item.created_at}</small>
                    </div>
                </div>
                <button type="button" class="mini-icon-btn" data-toggle-notification-read="${item.id}" title="Toggle read">
                    <i class="fa-solid fa-envelope-open-text"></i>
                </button>
            </div>
        `).join('') : '<div class="collaboration-empty">No notifications yet.</div>';
    }

    async function refreshNotifications() {
        const hasNotificationUi = document.querySelector('[data-notification-list]') || document.querySelector('[data-notification-badge]');
        if (!hasNotificationUi) return;
        const data = await apiFetch('/api/notifications/?limit=8');
        renderNotifications(data.items, data.unread_count);
    }

    async function toggleNotificationRead(notificationId, isRead) {
        await apiFetch(`/api/notifications/${notificationId}/read/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({ is_read: isRead }),
        });
        await refreshNotifications();
    }

    async function markAllNotificationsRead() {
        await apiFetch('/api/notifications/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
            },
        });
        await refreshNotifications();
    }

    async function refreshNotificationSettings() {
        const wrapper = document.querySelector('[data-notification-settings]');
        if (!wrapper) return;
        const data = await apiFetch('/api/notifications/settings/');
        wrapper.innerHTML = data.items.map(item => `
            <div class="setting-card">
                <div>
                    <strong>${item.label}</strong>
                    <p>In-app, email, SMS, and WhatsApp preferences.</p>
                </div>
                <label class="toggle-row">
                    <span>In App</span>
                    <input type="checkbox" data-setting-toggle="${item.category}" ${item.in_app_enabled ? 'checked' : ''}>
                </label>
            </div>
        `).join('');
    }

    function renderThreadList(items) {
        const panel = document.querySelector('[data-thread-list-panel]');
        const summary = document.querySelector('[data-thread-summary]');
        const unreadCount = items.filter(item => item.unread).length;
        if (summary) {
            summary.textContent = `${unreadCount} unread`;
        }
        updateBadge('[data-thread-badge]', unreadCount);
        if (!panel) return;
        panel.innerHTML = items.length ? items.map(item => `
            <a href="/communications/?thread=${item.id}" class="thread-card ${item.unread ? 'thread-card-unread' : ''}" data-thread-card data-thread-id="${item.id}">
                <strong>${item.title}</strong>
                <p>${item.scope} · ${item.status}</p>
                <small>${item.last_activity_at}</small>
            </a>
        `).join('') : '<div class="collaboration-empty">No threads yet.</div>';

        const topbarList = document.querySelector('[data-thread-list]');
        if (topbarList) {
            topbarList.innerHTML = items.slice(0, 6).length ? items.slice(0, 6).map(item => `
                <a href="/communications/?thread=${item.id}" class="collaboration-item ${item.unread ? 'is-unread' : ''}">
                    <div class="collaboration-item-main">
                        <div class="priority-dot priority-info"></div>
                        <div>
                            <strong>${item.title}</strong>
                            <p>${item.preview || item.scope}</p>
                            <small>${item.last_activity_at}</small>
                        </div>
                    </div>
                </a>
            `).join('') : '<div class="collaboration-empty">No communication threads yet.</div>';
        }
    }

    function renderThreadDetail(payload) {
        const title = document.querySelector('[data-thread-title]');
        const meta = document.querySelector('[data-thread-meta]');
        const entries = document.querySelector('[data-thread-entries]');
        const threadInput = document.querySelector('[data-thread-id-input]');
        if (title) title.textContent = payload.thread.title;
        if (meta) meta.textContent = `${payload.thread.scope} · ${payload.thread.status} · ${payload.thread.last_activity_at}`;
        if (threadInput) threadInput.value = payload.thread.id;
        if (!entries) return;
        entries.innerHTML = payload.entries.length ? payload.entries.map(entry => `
            <article class="comment-bubble ${entry.parent_id ? 'comment-reply' : ''}">
                <header>
                    <strong>${entry.author}</strong>
                    <span>${entry.role_label}</span>
                    <time>${entry.created_at}</time>
                </header>
                <p>${entry.body}</p>
                ${entry.mentions.length ? `<small>Mentions: ${entry.mentions.map(name => '@' + name).join(', ')}</small>` : ''}
                ${entry.attachment_url ? `<a href="${entry.attachment_url}" target="_blank" rel="noopener">Open attachment</a>` : ''}
            </article>
        `).join('') : '<div class="collaboration-empty">No comments in this thread yet.</div>';
    }

    async function loadThreads() {
        const form = document.querySelector('[data-thread-filter-form]');
        if (!form) return;
        const params = new URLSearchParams(new FormData(form));
        const data = await apiFetch(`/api/communications/threads/?${params.toString()}`);
        renderThreadList(data.items);
    }

    async function loadThreadDetail(threadId) {
        const data = await apiFetch(`/api/communications/threads/${threadId}/`);
        renderThreadDetail(data);
        await apiFetch(`/api/communications/threads/${threadId}/read/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCsrfToken() },
        });
        await loadThreads();
    }

    document.addEventListener('click', async function (event) {
        const toggleBtn = event.target.closest('[data-toggle-notification-read]');
        if (toggleBtn) {
            const item = toggleBtn.closest('[data-notification-item]');
            await toggleNotificationRead(toggleBtn.getAttribute('data-toggle-notification-read'), !(item && item.classList.contains('is-unread')));
            return;
        }

        if (event.target.closest('[data-mark-all-notifications]')) {
            await markAllNotificationsRead();
            return;
        }

        const threadCard = event.target.closest('[data-thread-card]');
        if (threadCard && document.querySelector('[data-communication-app]')) {
            event.preventDefault();
            await loadThreadDetail(threadCard.getAttribute('data-thread-id'));
        }
    });

    document.addEventListener('change', async function (event) {
        const toggle = event.target.closest('[data-setting-toggle]');
        if (toggle) {
            await apiFetch('/api/notifications/settings/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({
                    category: toggle.getAttribute('data-setting-toggle'),
                    in_app_enabled: toggle.checked,
                }),
            });
            return;
        }

        if (event.target.closest('[data-thread-filter-form]')) {
            await loadThreads();
        }
    });

    document.addEventListener('input', function (event) {
        if (event.target.closest('[data-thread-filter-form]')) {
            window.clearTimeout(window.__threadFilterTimer);
            window.__threadFilterTimer = window.setTimeout(loadThreads, 200);
        }
    });

    document.addEventListener('submit', async function (event) {
        const createForm = event.target.closest('[data-create-thread-form]');
        if (createForm) {
            event.preventDefault();
            const formData = new FormData(createForm);
            const payload = {
                title: formData.get('title'),
                scope: formData.get('scope'),
                object_id: String(formData.get('object_id') || '').trim(),
                assigned_to: formData.get('assigned_to'),
                tags: String(formData.get('tags') || '').split(',').map(item => item.trim()).filter(Boolean),
                visibility: String(formData.get('visibility') || '').split(',').map(item => item.trim()).filter(Boolean),
                body: formData.get('body'),
            };
            const data = await apiFetch('/api/communications/threads/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify(payload),
            });
            createForm.reset();
            await loadThreads();
            await loadThreadDetail(data.thread.id);
            return;
        }

        const commentForm = event.target.closest('[data-comment-form]');
        if (commentForm) {
            event.preventDefault();
            const threadId = commentForm.querySelector('[data-thread-id-input]')?.value;
            if (!threadId) return;
            const formData = new FormData(commentForm);
            await apiFetch(`/api/communications/threads/${threadId}/comment/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                },
                body: formData,
            });
            commentForm.reset();
            await loadThreadDetail(threadId);
        }
    });

    document.addEventListener('DOMContentLoaded', async function () {
        try {
            await refreshNotifications();
            await refreshNotificationSettings();
            if (document.querySelector('[data-communication-app]')) {
                await loadThreads();
                const threadId = new URLSearchParams(window.location.search).get('thread');
                if (threadId) {
                    await loadThreadDetail(threadId);
                }
            }
        } catch (error) {
            console.error('Collaboration UI error', error);
        }

        window.setInterval(function () {
            refreshNotifications().catch(() => {});
            if (document.querySelector('[data-communication-app]')) {
                loadThreads().catch(() => {});
            }
        }, 45000);
    });
})();
