/* =====================================================================
   static/js/script.js
   =====================================================================
   ALL the JavaScript for the site lives in this one file, wrapped in a
   DOMContentLoaded event so the elements are guaranteed to exist.

   IMPORTANT IDEA
   --------------
   JavaScript here only adds CONVENIENCE. The website still works with
   JavaScript switched off, because everything important (adding to the
   cart, logging in, checking out) happens through real HTML forms that
   POST to Flask routes on the server.
   ===================================================================== */

document.addEventListener('DOMContentLoaded', function () {

    /* =================================================================
       1. MOBILE HAMBURGER MENU
       Toggles the .open class that CSS uses to show/hide the menu.
       ================================================================= */
    const navToggle = document.getElementById('navToggle');
    const navMenu   = document.getElementById('navMenu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function () {
            const isOpen = navMenu.classList.toggle('open');
            navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });

        // Close the menu if the screen grows back to desktop size.
        window.addEventListener('resize', function () {
            if (window.innerWidth > 900) {
                navMenu.classList.remove('open');
                navToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }


    /* =================================================================
       2. FLASH MESSAGE CLOSE BUTTONS
       Lets the user dismiss a message instead of waiting for the reload.
       ================================================================= */
    document.querySelectorAll('.alert-close').forEach(function (button) {
        button.addEventListener('click', function () {
            const alert = button.closest('.alert');
            if (alert) { alert.remove(); }
        });
    });

    // Auto-hide info/success messages after a few seconds, but keep
    // error messages on screen (the user probably needs to read them).
    document.querySelectorAll('.alert-success, .alert-info').forEach(function (alert) {
        window.setTimeout(function () {
            alert.style.transition = 'opacity .4s';
            alert.style.opacity = '0';
            window.setTimeout(function () { alert.remove(); }, 400);
        }, 6000);
    });


    /* =================================================================
       3. CONFIRM BEFORE DANGEROUS ACTIONS
       Any <form data-confirm="..."> asks first. Used by delete buttons.
       ================================================================= */
    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            const question = form.getAttribute('data-confirm');
            if (!window.confirm(question)) {
                event.preventDefault();   // stop the form from sending
            }
        });
    });


    /* =================================================================
       4. QUANTITY INPUTS
       - Clicking the arrows can never go below 1 or above the stock.
       - Typing 0 is allowed (it means "remove this line"), but only in
         the cart, not on a product page.
       ================================================================= */
    document.querySelectorAll('input[type="number"][name="quantity"]').forEach(function (input) {
        const min = parseInt(input.getAttribute('min'), 10) || 0;
        const maxAttr = input.getAttribute('max');
        const max = maxAttr ? parseInt(maxAttr, 10) : null;

        // Used when the value comes from the "Cart" page.
        if (input.hasAttribute('data-qty-input')) {
            input.addEventListener('change', function () {
                let value = parseInt(input.value, 10);
                if (isNaN(value) || value < 0) {
                    value = 0;                     // 0 = remove the line
                }
                if (max !== null && value > max) {
                    value = max;
                    alert('Only ' + max + ' item(s) are available in stock.');
                }
                input.value = value;
            });
        } else {
            input.addEventListener('change', function () {
                let value = parseInt(input.value, 10);
                if (isNaN(value) || value < min) { value = min; }
                if (max !== null && value > max) {
                    value = max;
                    alert('Only ' + max + ' item(s) are available in stock.');
                }
                input.value = value;
            });
        }
    });


    /* =================================================================
       5. PASSWORD SHOW / HIDE BUTTON
       ================================================================= */
    document.querySelectorAll('.toggle-password').forEach(function (button) {
        button.addEventListener('click', function () {
            const box = button.closest('.password-box');
            const input = box ? box.querySelector('input') : null;
            if (!input) { return; }

            const showing = input.type === 'text';
            input.type = showing ? 'password' : 'text';
            button.textContent = showing ? 'Show' : 'Hide';
            button.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
        });
    });


    /* =================================================================
       6. PASSWORD STRENGTH METER  (registration page only)
       Four bars fill up as the password gets stronger.
       The REAL rule still lives on the server in app.py - this is only
       a hint for the visitor.
       ================================================================= */
    const passwordInput = document.getElementById('password');
    const meter = document.getElementById('strengthMeter');

    if (passwordInput && meter) {
        passwordInput.addEventListener('input', function () {
            const value = passwordInput.value;
            meter.className = 'strength-meter';

            if (!value) { return; }

            let score = 0;
            if (value.length >= 6)  { score++; }
            if (value.length >= 10) { score++; }
            if (/[A-Za-z]/.test(value) && /\d/.test(value)) { score++; }
            if (/[^A-Za-z0-9]/.test(value)) { score++; }

            if (score <= 1)      { meter.classList.add('weak'); }
            else if (score === 2) { meter.classList.add('fair'); }
            else if (score === 3) { meter.classList.add('good'); }
            else                  { meter.classList.add('strong'); }
        });
    }


    /* =================================================================
       7. SIMPLE CLIENT SIDE FORM CHECK  (checkout page)
       Gives instant feedback before the page is sent to the server.
       ================================================================= */
    const checkoutForm = document.getElementById('checkoutForm');

    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function (event) {
            let firstBadField = null;

            checkoutForm.querySelectorAll('input, textarea, select').forEach(function (field) {
                // Radio buttons are checked as a group below.
                if (field.type === 'radio') { return; }

                field.style.borderColor = '';
                const value = (field.value || '').trim();

                if (field.hasAttribute('required') && !value) {
                    field.style.borderColor = '#dc2626';
                    if (!firstBadField) { firstBadField = field; }
                    return;
                }

                // A 10 digit phone number, numbers only.
                if (field.type === 'tel' && value && !/^[0-9]{10}$/.test(value)) {
                    field.style.borderColor = '#dc2626';
                    if (!firstBadField) { firstBadField = field; }
                    return;
                }

                // A 6 digit PIN code, numbers only.
                if (field.name === 'pincode' && value && !/^[0-9]{6}$/.test(value)) {
                    field.style.borderColor = '#dc2626';
                    if (!firstBadField) { firstBadField = field; }
                    return;
                }

                // A basic email shape check.
                if (field.type === 'email' && value && !/^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/.test(value)) {
                    field.style.borderColor = '#dc2626';
                    if (!firstBadField) { firstBadField = field; }
                }
            });

            // At least one payment method must be chosen.
            const payments = checkoutForm.querySelectorAll('input[name="payment_method"]');
            if (payments.length && !checkoutForm.querySelector('input[name="payment_method"]:checked')) {
                if (!firstBadField) { firstBadField = payments[0]; }
            }

            if (firstBadField) {
                event.preventDefault();
                firstBadField.focus();
                alert('Please fill in all the required fields correctly.');
            }
        });
    }


    /* =================================================================
       8. IMAGE PREVIEW WHEN ADMIN CHOOSES A FILE
       ================================================================= */
    document.querySelectorAll('input[type="file"][data-preview-target]').forEach(function (input) {
        input.addEventListener('change', function () {
            const file = input.files && input.files[0];
            if (!file) { return; }

            // Rough size check so the user is told before the upload fails.
            const maxBytes = 2 * 1024 * 1024;
            if (file.size > maxBytes) {
                alert('That image is larger than 2 MB. Please pick a smaller file.');
                input.value = '';
                return;
            }

            const preview = document.getElementById(input.getAttribute('data-preview-target'));
            if (!preview) { return; }

            // FileReader reads the file that is already on the computer,
            // so this preview works even before the page is saved.
            const reader = new FileReader();
            reader.onload = function (event) { preview.src = event.target.result; };
            reader.readAsDataURL(file);
        });
    });


    /* =================================================================
       9. BACK TO TOP BUTTON  (appears after scrolling down)
       ================================================================= */
    const toTop = document.getElementById('toTop');

    if (toTop) {
        window.addEventListener('scroll', function () {
            toTop.hidden = window.scrollY < 400;
        }, { passive: true });

        toTop.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }


    /* =================================================================
       10. USER DROPDOWN ON TOUCH DEVICES
       On a phone there is no hover, so tap needs to open the menu.
       ================================================================= */
    document.querySelectorAll('.dropdown-toggle').forEach(function (button) {
        button.addEventListener('click', function (event) {
            const menu = button.nextElementSibling;
            if (!menu) { return; }

            // Only needed on narrow screens; CSS handles hover on desktop.
            if (window.innerWidth > 900) { return; }

            event.stopPropagation();
            menu.classList.toggle('show');
        });
    });

    document.addEventListener('click', function () {
        document.querySelectorAll('.dropdown-menu.show').forEach(function (menu) {
            menu.classList.remove('show');
        });
    });


    /* =================================================================
       11. REFRESH THE CART BADGE
       Fetches /api/cart-count with fetch() and updates the navbar badge
       if the number changed. Nice demonstration of calling an API.
       ================================================================= */
    function refreshCartCount() {
        const badge = document.getElementById('cartCount');
        if (!badge) { return; }

        fetch('/api/cart-count', { headers: { 'X-Requested-With': 'fetch' } })
            .then(function (response) {
                if (!response.ok) { throw new Error('Request failed'); }
                return response.json();
            })
            .then(function (data) {
                const count = parseInt(data.count, 10) || 0;
                badge.textContent = count;
                badge.classList.toggle('hidden', count === 0);
            })
            .catch(function () {
                // Silently ignore - the badge is not important enough to
                // bother the user with an error.
            });
    }

    // Refresh whenever the tab regains focus (for example after checkout).
    window.addEventListener('focus', refreshCartCount);


    /* =================================================================
       12. FADE IN SECTIONS AS THEY SCROLL INTO VIEW
       -----------------------------------------------------------------
       A tiny IntersectionObserver, purely for looks.

       WHY THE "can-animate" CLASS MATTERS
       Every [data-animate] element is VISIBLE by default. We only add
       .can-animate to <html> once we have confirmed the observer exists
       and will run. So if this file never loads, is blocked, or throws
       an error, the class is never added and every section stays
       visible. An earlier version set opacity from JS directly, which
       meant any JS failure left the whole shop blank.
       ================================================================= */
    const revealTargets = document.querySelectorAll('[data-animate]');
    const supportsObserver = 'IntersectionObserver' in window;
    const prefersStill = window.matchMedia
        && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (revealTargets.length && supportsObserver && !prefersStill) {
        document.documentElement.classList.add('can-animate');

        const revealObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-view');
                    revealObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -50px 0px' });

        revealTargets.forEach(function (el) { revealObserver.observe(el); });

        // Safety net: after 4 seconds show everything unconditionally,
        // and switch the transition OFF so a stalled animation cannot
        // leave content invisible.
        window.setTimeout(function () {
            document.querySelectorAll('[data-animate]').forEach(function (el) {
                el.style.transition = 'none';
                el.classList.add('in-view');
            });
            document.documentElement.classList.remove('can-animate');
            revealObserver.disconnect();
        }, 4000);
    }


    /* =================================================================
       13. TOAST NOTIFICATIONS
       -----------------------------------------------------------------
       showToast() is deliberately global because it is also called from
       the onsubmit handler in contact.html and the newsletter box.
       ================================================================= */
    const TOAST_ICONS = {
        success: '\u2713',
        error:   '\u2717',
        warning: '!',
        info:    'i'
    };

    window.showToast = function (message, type, duration) {
        const area = document.getElementById('toastArea');
        if (!area || !message) { return; }

        const kind = TOAST_ICONS[type] ? type : 'info';
        const toast = document.createElement('div');
        toast.className = 'toast toast-' + kind;
        toast.setAttribute('role', kind === 'error' ? 'alert' : 'status');

        const icon = document.createElement('span');
        icon.className = 'toast-icon';
        icon.textContent = TOAST_ICONS[kind];

        const text = document.createElement('span');
        text.className = 'toast-text';
        text.textContent = message;          // textContent, never innerHTML

        const close = document.createElement('button');
        close.className = 'toast-close';
        close.type = 'button';
        close.setAttribute('aria-label', 'Dismiss');
        close.innerHTML = '&times;';

        toast.appendChild(icon);
        toast.appendChild(text);
        toast.appendChild(close);
        area.appendChild(toast);

        let timer = null;
        const dismiss = function () {
            if (!toast.parentNode) { return; }
            window.clearTimeout(timer);
            toast.classList.add('out');
            window.setTimeout(function () { toast.remove(); }, 260);
        };

        close.addEventListener('click', dismiss);
        timer = window.setTimeout(dismiss, duration || 3600);

        // Never let more than four toasts pile up.
        while (area.children.length > 4) { area.firstElementChild.remove(); }
    };


    /* =================================================================
       14. TURN FLASH MESSAGES INTO TOASTS
       -----------------------------------------------------------------
       Flask's flash() messages render as .alert boxes. We copy them
       into the toast area so every notification looks the same, then
       hide the original. The original stays in the DOM (hidden by CSS)
       so no information is lost if JavaScript is unavailable.
       ================================================================= */
    document.querySelectorAll('.alert').forEach(function (alert) {
        const textNode = alert.querySelector('.alert-text');
        if (!textNode) { return; }

        const text = (textNode.textContent || '').trim();
        if (!text) { return; }

        let kind = 'info';
        if (alert.classList.contains('alert-success')) { kind = 'success'; }
        else if (alert.classList.contains('alert-error')) { kind = 'error'; }
        else if (alert.classList.contains('alert-warning')) { kind = 'warning'; }

        alert.classList.add('alert-moved');     // hidden via CSS
        window.showToast(text, kind, kind === 'error' ? 6500 : 3600);
    });


    /* =================================================================
       15. ADD TO CART FEEDBACK
       -----------------------------------------------------------------
       The form still posts to Flask exactly as before. We only add a
       spinner and a toast so the click feels responsive. No cart logic
       is touched.
       ================================================================= */
    document.querySelectorAll(
        'form[action*="/cart/add"] button[type="submit"], ' +
        '[data-add-form] button[type="submit"]'
    ).forEach(function (button) {
        button.addEventListener('click', function () {
            const form = button.closest('form');
            if (!form) { return; }

            const card = button.closest('.product-card, .offer-card');
            const nameEl = card
                ? card.querySelector('.product-title a, .offer-body h3 a')
                : null;
            const name = nameEl ? nameEl.textContent.trim() : '';

            button.classList.add('is-loading');

            // Fires just before the page navigates away. A nicety, not
            // the source of truth - the Flask flash message is.
            window.setTimeout(function () {
                window.showToast(
                    name ? name + ' added to cart!' : 'Product added to cart!',
                    'success', 2400
                );
            }, 260);
        });
    });


    /* =================================================================
       16. LOADING SPINNER ON FORM SUBMIT
       ----------------------------------------------------------------- */
    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function () {
            const button = form.querySelector('button[type="submit"]');
            if (!button) { return; }

            // Wait briefly so any inline onsubmit handler runs first.
            window.setTimeout(function () {
                button.classList.add('is-loading');
            }, 60);
        });
    });


    /* =================================================================
       17. IMAGE FALLBACK
       -----------------------------------------------------------------
       Templates also carry an onerror attribute; this catches anything
       those missed so a dead URL never leaves a broken-image icon.
       ================================================================= */
    const PLACEHOLDER = '/static/images/placeholder.svg';

    document.querySelectorAll('img').forEach(function (img) {
        img.addEventListener('error', function () {
            if (img.dataset.fallbackApplied) { return; }
            img.dataset.fallbackApplied = '1';
            img.src = PLACEHOLDER;
        });
    });


    /* =================================================================
       18. PRODUCT DETAIL QUANTITY STEPPER
       ================================================================= */
    document.querySelectorAll('.qty-stepper').forEach(function (stepper) {
        const input = stepper.querySelector('input[name="quantity"]');
        if (!input) { return; }

        const min = parseInt(input.getAttribute('min'), 10) || 1;
        const maxAttr = input.getAttribute('max');
        const max = maxAttr ? parseInt(maxAttr, 10) : null;

        stepper.querySelectorAll('.qty-btn').forEach(function (button) {
            button.addEventListener('click', function () {
                const step = parseInt(button.dataset.step, 10) || 0;
                let value = (parseInt(input.value, 10) || min) + step;

                if (value < min) { value = min; }
                if (max && value > max) {
                    value = max;
                    window.showToast('Only ' + max + ' available in stock.', 'warning');
                }
                input.value = value;
            });
        });
    });


    /* =================================================================
       19. INSTANT CLIENT-SIDE FILTER  (products page)
       -----------------------------------------------------------------
       PURELY a convenience layer. The page already filters on the
       server through ?q= and ?category=, which still works with
       JavaScript off, and the real filter form below is untouched.

       What this adds: as you type, the cards already on the page hide
       or show instantly instead of waiting for a page reload.
       ================================================================= */
    const quickGrid = document.getElementById('quickFilter');
    const quickSearch = document.getElementById('quickSearch');
    const quickCategory = document.getElementById('quickCategory');
    const quickSort = document.getElementById('quickSort');
    const quickCount = document.getElementById('quickCount');
    const quickEmpty = document.getElementById('quickEmpty');
    const quickSearchAll = document.getElementById('quickSearchAll');

    if (quickGrid) {
        const cards = Array.from(quickGrid.querySelectorAll('.product-card'));

        // Read the data-* attributes once; never scrape visible text.
        cards.forEach(function (card, index) {
            card.dataset.search = (card.dataset.name || '').toLowerCase();
            card.dataset.idx = String(index);
        });

        const applyFilter = function () {
            const term = (quickSearch.value || '').trim().toLowerCase();
            const category = quickCategory ? quickCategory.value : '';
            let shown = 0;

            cards.forEach(function (card) {
                const matchesTerm =
                    !term || card.dataset.search.indexOf(term) !== -1;
                const matchesCat =
                    !category || card.dataset.category === category;
                const visible = matchesTerm && matchesCat;

                card.style.display = visible ? '' : 'none';
                if (visible) { shown++; }
            });

            if (quickCount) {
                quickCount.textContent = shown === cards.length
                    ? cards.length + ' products on this page'
                    : shown + ' of ' + cards.length + ' on this page';
            }
            if (quickEmpty) { quickEmpty.classList.toggle('show', shown === 0); }
            quickGrid.style.display = shown === 0 ? 'none' : '';

            // Point the "search everything" link at whatever was typed,
            // so one click runs a real full-catalogue search on the server.
            if (quickSearchAll) {
                quickSearchAll.href = term
                    ? '/products?q=' + encodeURIComponent(term)
                    : '/products';
            }
        };

        // Client-side re-sort. Reordering the DOM needs no server call.
        if (quickSort) {
            quickSort.addEventListener('change', function () {
                const mode = quickSort.value;
                const sorted = cards.slice().sort(function (a, b) {
                    const pa = parseFloat(a.dataset.price) || 0;
                    const pb = parseFloat(b.dataset.price) || 0;
                    const na = a.dataset.name || '';
                    const nb = b.dataset.name || '';

                    if (mode === 'price_low')  { return pa - pb; }
                    if (mode === 'price_high') { return pb - pa; }
                    if (mode === 'name')       { return na.localeCompare(nb); }
                    return parseInt(a.dataset.idx, 10) - parseInt(b.dataset.idx, 10);
                });
                sorted.forEach(function (card) { quickGrid.appendChild(card); });
            });
        }

        if (quickSearch)  { quickSearch.addEventListener('input', applyFilter); }
        if (quickCategory){ quickCategory.addEventListener('change', applyFilter); }

        const quickClear = document.getElementById('quickClear');
        if (quickClear) {
            quickClear.addEventListener('click', function () {
                if (quickSearch)   { quickSearch.value = ''; }
                if (quickCategory) { quickCategory.value = ''; }
                applyFilter();
            });
        }

        // The "no matches" panel has its own reset button.
        const quickClearEmpty = document.getElementById('quickClearEmpty');
        if (quickClearEmpty && quickClear) {
            quickClearEmpty.addEventListener('click', function () {
                quickClear.click();
            });
        }

        applyFilter();
    }

});