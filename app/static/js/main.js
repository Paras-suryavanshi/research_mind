/* Shared behavior. Page templates retain their inline handlers for progressive enhancement. */
(function () {
    'use strict';
    window.toggleSidebar = window.toggleSidebar || function () {
        var sidebar = document.getElementById('sidebar');
        var overlay = document.getElementById('mobile-overlay');
        if (!sidebar || !overlay) return;
        sidebar.classList.toggle('open');
        overlay.classList.toggle('show');
    };
    window.autoResize = window.autoResize || function (textarea) {
        if (!textarea) return;
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    };
    document.addEventListener('DOMContentLoaded', function () {
        var list = document.getElementById('recent-searches-list');
        if (!list || !window.location.pathname.startsWith('/')) return;
        fetch('/api/history/searches')
            .then(function (response) { return response.ok ? response.json() : null; })
            .then(function (data) {
                if (!data || !data.items) return;
                list.innerHTML = '';
                data.items.slice(0, 5).forEach(function (item) {
                    var link = document.createElement('a');
                    link.className = 'nav-item recent-search-item';
                    link.href = '/dashboard?query=' + encodeURIComponent(item.query);
                    link.textContent = item.query;
                    list.appendChild(link);
                });
                if (!data.items.length) {
                    list.innerHTML = '<span class="nav-item" style="color: var(--text-secondary);">No searches yet</span>';
                }
            })
            .catch(function () {});
    });
})();