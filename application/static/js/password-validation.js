/**
 * Password validation module
 * Handles registration form password validation and UI updates
 */

/**
 * Validates username field
 * @param {HTMLInputElement} usernameInput - The username input element
 * @returns {boolean} True if username is valid
 */
export function validateUsername(usernameInput) {
  return usernameInput && usernameInput.value.trim().length > 0;
}

/**
 * Validates password strength
 * @param {string} password - The password to validate
 * @param {Object} rules - Rule elements { ruleLength, ruleUpper, ruleNumber, ruleSpecial }
 * @returns {boolean} True if password meets all requirements
 */
export function validatePassword(password, rules) {
  const val = password || '';

  const hasLength = val.length >= 8;
  const hasUpper = /[A-Z]/.test(val);
  const hasNumber = /\d/.test(val);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>_\-\/\[\]\\]/.test(val);

  if (rules) {
    updateRule(rules.ruleLength, hasLength);
    updateRule(rules.ruleUpper, hasUpper);
    updateRule(rules.ruleNumber, hasNumber);
    updateRule(rules.ruleSpecial, hasSpecial);
  }

  return hasLength && hasUpper && hasNumber && hasSpecial;
}

/**
 * Validates password confirmation
 * @param {string} password - The password
 * @param {string} passwordConfirm - The confirmation password
 * @param {HTMLElement} mismatchElement - Element to show mismatch message
 * @returns {boolean} True if passwords match
 */
export function validatePasswordMatch(password, passwordConfirm, mismatchElement) {
  const match = password === passwordConfirm && passwordConfirm.length > 0;

  if (mismatchElement) {
    mismatchElement.classList.toggle('hidden', match);
  }

  return match;
}

/**
 * Validates email is SFSU email
 * @param {string} email - The email to validate
 * @param {HTMLElement} emailHint - Element to show email hint
 * @param {HTMLInputElement} emailInput - The email input element
 * @returns {boolean} True if email is valid SFSU email
 */
export function validateEmail(email, emailHint, emailInput) {
  const val = email ? email.trim() : '';
  const valid = val.endsWith('@sfsu.edu');

  if (val.length > 0 && !valid && emailHint && emailInput) {
    emailHint.classList.remove('hidden');
    emailInput.style.borderColor = '#ef4444';
  } else if (emailHint && emailInput) {
    emailHint.classList.add('hidden');
    emailInput.style.borderColor = '#d1d5db';
  }

  return valid;
}

/**
 * Updates rule element styling
 * @param {HTMLElement} ruleElement - The rule element to update
 * @param {boolean} valid - Whether the rule is satisfied
 */
export function updateRule(ruleElement, valid) {
  if (!ruleElement) return;

  ruleElement.style.textDecoration = valid ? 'line-through' : 'none';
  ruleElement.style.color = valid ? '#16a34a' : '#374151';
}

/**
 * Updates submit button state based on form validity
 * @param {HTMLElement} submitBtn - The submit button
 * @param {Object} formElements - Form element references
 * @param {boolean} hasServerErrors - Whether form has server-side errors
 */
export function updateSubmitState(submitBtn, formElements, hasServerErrors) {
  if (!submitBtn) return;

  if (hasServerErrors) {
    submitBtn.disabled = false;
    submitBtn.classList.remove('bg-slate-400', 'cursor-not-allowed');
    submitBtn.classList.add('bg-slate-900', 'hover:bg-slate-700');
    return;
  }

  const emailValid = validateEmail(
    formElements.email?.value,
    formElements.emailHint,
    formElements.email
  );
  const passwordValid = validatePassword(formElements.password?.value, formElements.rules);
  const passwordsMatch = validatePasswordMatch(
    formElements.password?.value || '',
    formElements.passwordConfirm?.value || '',
    formElements.passwordMatch
  );
  const usernameValid = validateUsername(formElements.username);

  const allValid = emailValid && passwordValid && passwordsMatch && usernameValid;

  submitBtn.disabled = !allValid;
  if (allValid) {
    submitBtn.classList.remove('bg-slate-400', 'cursor-not-allowed');
    submitBtn.classList.add('bg-slate-900', 'hover:bg-slate-700');
  } else {
    submitBtn.classList.add('bg-slate-400', 'cursor-not-allowed');
    submitBtn.classList.remove('bg-slate-900', 'hover:bg-slate-700');
  }
}

/**
 * Initializes password validation on the registration form
 * Should be called once when registration page is ready
 */
export function initPasswordValidation() {
  const password = document.getElementById('password1');
  const password2 = document.getElementById('password2');
  const rulesBox = document.getElementById('passwordRules');
  const email = document.getElementById('email');
  const emailHint = document.getElementById('emailHint');
  const username = document.getElementById('username');
  const submitBtn = document.getElementById('submitBtn');
  const passwordMatch = document.getElementById('passwordMatch');

  const ruleLength = document.getElementById('rule-length');
  const ruleUpper = document.getElementById('rule-upper');
  const ruleNumber = document.getElementById('rule-number');
  const ruleSpecial = document.getElementById('rule-special');

  // Check if form has server errors
  const hasServerErrors = document.querySelector('[data-has-errors]')?.dataset.hasErrors === 'true';

  const formElements = {
    password,
    passwordConfirm: password2,
    email,
    emailHint,
    username,
    passwordMatch,
    rules: { ruleLength, ruleUpper, ruleNumber, ruleSpecial }
  };

  // PASSWORD RULES UI
  if (rulesBox && password) {
    password.addEventListener('focus', () => {
      rulesBox.classList.remove('hidden');
    });

    password.addEventListener('blur', () => {
      setTimeout(() => {
        if (!password.matches(':focus')) {
          rulesBox.classList.add('hidden');
        }
      }, 150);
    });
  }

  // VALIDATION EVENTS
  if (password) {
    password.addEventListener('input', () => updateSubmitState(submitBtn, formElements, hasServerErrors));
  }
  if (password2) {
    password2.addEventListener('input', () => updateSubmitState(submitBtn, formElements, hasServerErrors));
  }
  if (email) {
    email.addEventListener('input', () => updateSubmitState(submitBtn, formElements, hasServerErrors));
  }
  if (username) {
    username.addEventListener('input', () => updateSubmitState(submitBtn, formElements, hasServerErrors));
  }

  // Initial state
  updateSubmitState(submitBtn, formElements, hasServerErrors);
}
