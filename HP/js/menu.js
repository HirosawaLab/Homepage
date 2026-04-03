(function () {
  function init() {
    var hamburger = document.querySelector('.hamburger');
    if (!hamburger) return;

    // オーバーレイ
    var overlay = document.createElement('div');
    overlay.id = 'menu-overlay';

    // ドロワー
    var drawer = document.createElement('div');
    drawer.id = 'menu-drawer';

    // 閉じるボタン
    var closeBtn = document.createElement('button');
    closeBtn.id = 'menu-close-btn';
    closeBtn.setAttribute('aria-label', '閉じる');
    closeBtn.innerHTML = '<span></span><span></span>';

    // global-nav のリンクをクローン
    var globalNav = document.querySelector('.global-nav');
    var drawerNav = document.createElement('nav');
    drawerNav.id = 'menu-drawer-nav';
    if (globalNav) {
      var ul = globalNav.querySelector('ul').cloneNode(true);
      drawerNav.appendChild(ul);
    }

    drawer.appendChild(closeBtn);
    drawer.appendChild(drawerNav);
    overlay.appendChild(drawer);
    document.body.appendChild(overlay);

    function openMenu() {
      overlay.classList.add('is-open');
      hamburger.classList.add('is-active');
      document.body.classList.add('menu-open');
    }

    function closeMenu() {
      overlay.classList.remove('is-open');
      hamburger.classList.remove('is-active');
      document.body.classList.remove('menu-open');
    }

    // <a> に pointer-events:none を設定済みのため hamburger div に直接当たる
    hamburger.addEventListener('click', function (e) {
      e.preventDefault();
      openMenu();
    });

    closeBtn.addEventListener('click', closeMenu);

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeMenu();
    });

    drawerNav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', closeMenu);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
