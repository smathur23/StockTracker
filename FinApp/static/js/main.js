document.addEventListener('DOMContentLoaded', (event) => {
    document.querySelectorAll('.delete-link').forEach(link => {
        link.addEventListener('click', (event) => {
            if (!confirm('Are you sure you want to delete this stock?')) {
                event.preventDefault();
            }
        });
    });

    const tickerInput = document.getElementById('ticker-input');
    tickerInput.addEventListener('focus', () => {
        tickerInput.placeholder = '';
    });

    tickerInput.addEventListener('blur', () => {
        tickerInput.placeholder = 'Enter stock ticker';
    });

    const passwordInput = document.getElementById('password');
    const togglePassword = document.createElement('span');
    togglePassword.textContent = 'Show';
    togglePassword.style.cursor = 'pointer';
    togglePassword.style.marginLeft = '10px';

    passwordInput.parentNode.insertBefore(togglePassword, passwordInput.nextSibling);

    togglePassword.addEventListener('click', () => {
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            togglePassword.textContent = 'Hide';
        } else {
            passwordInput.type = 'password';
            togglePassword.textContent = 'Show';
        }
    });
});
