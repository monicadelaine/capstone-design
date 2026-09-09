<script setup>
import { computed, onMounted, watch, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuth0 } from '@auth0/auth0-vue';

const { loginWithRedirect, isLoading, isAuthenticated, user } = useAuth0();
const route = useRoute();
const router = useRouter();

// Modal state
const showSignupModal = ref(false);

// Error handling (kept exactly as you had it)
const error = computed(() => route.query.error || null);
const errorDescription = computed(() => route.query.error_description || null);

const isUnverifiedEmail = computed(() =>
        error.value === 'access_denied' && errorDescription.value?.toLowerCase().includes('unverified_email')
);

const isInvalidStudentDomain = computed(() =>
        error.value === 'access_denied' && errorDescription.value?.toLowerCase().includes('invalid_student_domain')
);

const unverifiedEmailFromError = computed(() => {
        if (!errorDescription.value) return null;
        const emailMatch = errorDescription.value.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
        return emailMatch ? emailMatch[0] : null;
});

const userEmail = computed(() => unverifiedEmailFromError.value || null);

const clearError = () => router.replace({ path: '/', query: {} });

const redirectByRole = () => {
        const roles = user.value?.['https://backend-api-capstone/roles'] ?? [];
        if (roles.includes('student')) {
                router.push('/student');
        } else if (roles.includes('sponsor')) {
                router.push('/sponsor');
        } else {
                router.push('/?error=no_role');
        }
};

// Modal controls
const openSignupModal = () => { showSignupModal.value = true; };
const closeSignupModal = () => { showSignupModal.value = false; };

// Handle login
const handleLogin = () => {
        loginWithRedirect({ authorizationParams: { screen_hint: 'login' } });
};

const handleSignup = (role) => {
	closeSignupModal();
	
	// Pass role as a custom scope instead of query parameter
	// Format: 'openid profile email role:student' or 'role:sponsor'
	const baseScopes = 'openid profile email';
	const roleScope = `role:${role}`;
	
	loginWithRedirect({
		authorizationParams: {
			screen_hint: 'signup',
			scope: `${baseScopes} ${roleScope}`,
			...(role === 'student' && { connection: 'Username-Password-Authentication' })
		}
	});
};

// Already-authenticated users landing on this page
onMounted(() => {
        if (isAuthenticated.value && !isLoading.value) {
                redirectByRole();
        }
});

watch([isAuthenticated, isLoading], ([authed, loading]) => {
        if (authed && !loading) {
                redirectByRole();
        }
});</script>

<template>
        <div class="login-container">
                <div class="login-card">
                        <h1>Capstone Project Manager</h1>

                        <div v-if="error === 'no_role'" class="error-message">
                                <strong>Authentication Error</strong>
                                <p>No role found in your account. Please contact your administrator to be assigned a
                                        role (Student or Sponsor).</p>
                        </div>

                        <!-- Email Verification Required -->
                        <div v-else-if="isUnverifiedEmail" class="verification-message">
                                <h2>Verify Your Email</h2>
                                <p>Check your inbox for a verification link. Make sure to
                                        check your spam folder.</p>
                                <p v-if="userEmail" class="verification-email">
                                        <strong>Email:</strong> {{ userEmail }}
                                </p>
                                <button @click="clearError" class="btn-primary">
                                        Back to Login
                                </button>
                                <p class="verification-help">Once verified, click above to return to the login page.</p>
                        </div>

                        <!-- Invalid Student Domain Error -->
                        <div v-else-if="isInvalidStudentDomain" class="error-message">
                                <strong>@crimson.ua.edu Required</strong>
                                <p>Student accounts must use a university email address (@crimson.ua.edu). Please sign
                                        up as a sponsor or use your university email.</p>
                        </div>

                        <div v-else-if="isLoading" class="loading">Loading...</div>

                        <!-- Main action buttons -->
                        <div v-else class="login-buttons main-actions">
                                <button @click="handleLogin" class="btn-login">
                                        Login
                                </button>
                                <button @click="openSignupModal" class="btn-signup">
                                        Sign Up
                                </button>
                        </div>
                </div>

                <!-- Role Selection Modal -->
                <div v-if="showSignupModal" class="modal-backdrop" @click="closeSignupModal">
                        <div class="modal-content" @click.stop>
                                <button class="modal-close" @click="closeSignupModal">×</button>
                                <h3>Sign Up As</h3>
                                <p class="modal-subtitle">Select your role to continue</p>
                                <div class="role-buttons">
                                        <button @click="handleSignup('student')" class="btn-student">
                                                I am a Student
                                        </button>
                                        <p class="role-restriction">Requires @crimson.ua.edu email</p>
                                        <button @click="handleSignup('sponsor')" class="btn-sponsor">
                                                I am a Sponsor
                                        </button>
                                        <p class="role-restriction">Any email address</p>
                                </div>
                        </div>
                </div>
        </div>
</template>

<style scoped>
.login-container {
        /* background-image: url(https://rolltide.com/images/2024/12/3/082723_ADMIN_ShelbyQuad_Campus_CLized.jpg); */
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: calc(100vh - 4rem);
        margin-top: 2rem;
        gap: 2rem;
        padding: 2rem;
}

.login-card {
        background: rgb(255, 255, 255);
        padding: 3rem;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        width: 100%;
        max-width: 500px;
        text-align: center;
}

h1 {
        font-size: 2.25rem;
        margin: 0 0 2rem 0;
        color: var(--text-default);
}

.subtitle {
        color: var(--text-subtle);
        margin: 0 0 2rem 0;
        font-size: 1rem;
}

.error-message {
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        text-align: left;
}

.error-message strong {
        display: block;
        margin-bottom: 0.5rem;
}

.error-message p {
        margin: 0;
        font-size: 0.9rem;
}

.login-buttons {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        width: 100%;
}

button {
        padding: 1rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
}

button:hover {
        /* transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); */
}

.btn-student {
        background-color: var(--accent-primary);
        color: white;
}

.btn-student:hover {
        filter: brightness(.9);
}

.btn-sponsor {
        background-color: #757c88;
        color: white;
}

.btn-sponsor:hover {
        background-color: #5a5d66;
}

.loading {
        font-size: 1rem;
        color: var(--text-subtle);
}

/* Email Verification Styles */
.verification-message {
        background: var(--background-info);
        border: 2px solid var(--accent-info);
        color: var(--text-info);
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1.5rem;
}

.verification-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
}

.verification-message h2 {
        font-size: 1.75rem;
        margin: 0 0 1rem 0;
        color: var(--text-info);
}

.verification-message p {
        font-size: 1rem;
        line-height: 1.6;
        margin: 0 0 1rem 0;
}

.verification-message .verification-hint {
        font-size: 0.9rem;
        color: var(--text-subtle);
        margin-bottom: 1.5rem;
}

.verification-message .verification-email {
        font-size: 1rem;
        color: var(--text-default);
        background: rgba(255, 255, 255, 0.5);
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin: 0 0 1rem 0;
        word-break: break-all;
}

.verification-message .verification-help {
        font-size: 0.8rem;
        color: var(--text-subtle);
        margin-top: 1rem;
        margin-bottom: 0;
}

.btn-primary {
        padding: 0.75rem 2rem;
}



/* Main action buttons */
.main-actions {
        gap: 1.5rem;
}

.btn-login {
        background-color: var(--accent-primary);
        color: white;
}

.btn-login:hover {
        filter: brightness(0.9);
}

.btn-signup {
        background-color: transparent;
        color: var(--accent-primary);
        border: 2px solid var(--accent-primary);
}

.btn-signup:hover {
        background-color: var(--accent-primary);
        color: white;
        filter: brightness(0.9);
}

/* Modal Styles */
.modal-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
        from {
                opacity: 0;
        }

        to {
                opacity: 1;
        }
}

.modal-content {
        background: white;
        padding: 2.5rem;
        border-radius: 16px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        max-width: 450px;
        width: 90%;
        position: relative;
        animation: slideUp 0.3s ease;
}

@keyframes slideUp {
        from {
                opacity: 0;
                transform: translateY(20px);
        }

        to {
                opacity: 1;
                transform: translateY(0);
        }
}

.modal-close {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: none;
        border: none;
        font-size: 1.5rem;
        color: var(--text-subtle);
        cursor: pointer;
        padding: 0.25rem;
        line-height: 1;
        transition: color 0.2s ease;
}

.modal-close:hover {
        color: var(--text-default);
        transform: none;
        box-shadow: none;
}

.modal-content h3 {
        font-size: 1.5rem;
        margin: 0 0 0.5rem 0;
        color: var(--text-default);
}

.modal-subtitle {
        color: var(--text-subtle);
        font-size: 0.95rem;
        margin: 0 0 1.5rem 0;
}

.role-buttons {
        display: flex;
        flex-direction: column;
        gap: 1rem;
}

.role-restriction {
        font-size: 0.8rem;
        color: var(--text-subtle);
        margin: -0.75rem 0 0.5rem 0;
        font-style: italic;
}
</style>
