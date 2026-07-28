import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import Spinner from '../components/Spinner';

interface FormErrors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

interface PasswordRequirements {
  hasLetter: boolean;
  hasNumber: boolean;
  hasMinLength: boolean;
}

function validateName(name: string): string | undefined {
  if (!name.trim()) return 'Name is required';
  if (name.trim().length < 2) return 'Name must be at least 2 characters';
  return undefined;
}

function validateEmail(email: string): string | undefined {
  if (!email) return 'Email is required';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Invalid email format';
  return undefined;
}

function validatePassword(password: string): string | undefined {
  if (!password) return 'Password is required';
  if (password.length < 6) return 'Password must be at least 6 characters';
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) return 'Password must include letters and numbers';
  return undefined;
}

function checkPasswordRequirements(password: string): PasswordRequirements {
  return {
    hasLetter: /[A-Za-z]/.test(password),
    hasNumber: /\d/.test(password),
    hasMinLength: password.length >= 6,
  };
}

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');
  const passwordRequirements = checkPasswordRequirements(password);
  const isPasswordValid = passwordRequirements.hasLetter && passwordRequirements.hasNumber && passwordRequirements.hasMinLength;
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setApiError('');

    const nameErr = validateName(name);
    const emailErr = validateEmail(email);
    const passErr = validatePassword(password);
    const confirmErr =
      password !== confirmPassword ? 'Passwords do not match' : undefined;

    setErrors({ name: nameErr, email: emailErr, password: passErr, confirmPassword: confirmErr });

    if (nameErr || emailErr || passErr || confirmErr) return;

    setLoading(true);
    try {
      await register({ name: name.trim(), email, password });
      navigate('/');
    } catch {
      setApiError('Registration failed. Try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(e.target.value);
    if (errors.password) {
      const newError = validatePassword(e.target.value);
      setErrors(prev => ({ ...prev, password: newError }));
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Create Account</h1>
        <p className="auth-subtitle">Register for Test App</p>

        {apiError && <div className="alert alert-error">{apiError}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="name">Full Name</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={errors.name ? 'input-error' : ''}
              placeholder="John Doe"
              autoComplete="name"
            />
            {errors.name && <span className="field-error">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={errors.email ? 'input-error' : ''}
              placeholder="you@example.com"
              autoComplete="email"
            />
            {errors.email && <span className="field-error">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={handlePasswordChange}
              className={errors.password ? 'input-error' : ''}
              placeholder="Min 6 chars, letters & numbers"
              autoComplete="new-password"
            />
            {errors.password && <span className="field-error">{errors.password}</span>}
            {password.length > 0 && (
              <div className="password-requirements">
                <div className={`requirement ${passwordRequirements.hasMinLength ? 'met' : 'unmet'}`}>
                  <span className="requirement-icon">{passwordRequirements.hasMinLength ? '✓' : '✗'}</span>
                  <span>At least 6 characters</span>
                </div>
                <div className={`requirement ${passwordRequirements.hasLetter ? 'met' : 'unmet'}`}>
                  <span className="requirement-icon">{passwordRequirements.hasLetter ? '✓' : '✗'}</span>
                  <span>At least one letter</span>
                </div>
                <div className={`requirement ${passwordRequirements.hasNumber ? 'met' : 'unmet'}`}>
                  <span className="requirement-icon">{passwordRequirements.hasNumber ? '✓' : '✗'}</span>
                  <span>At least one number</span>
                </div>
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={errors.confirmPassword ? 'input-error' : ''}
              placeholder="Repeat password"
              autoComplete="new-password"
            />
            {errors.confirmPassword && <span className="field-error">{errors.confirmPassword}</span>}
          </div>

          <button type="submit" className="btn btn-primary btn-block" disabled={loading || !isPasswordValid}>
            {loading ? (
              <>
                <Spinner size="sm" ariaLabel="Creating account" />
                <span>Creating account...</span>
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
