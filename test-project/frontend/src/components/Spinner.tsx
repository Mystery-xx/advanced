import './Spinner.css';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  ariaLabel?: string;
}

export default function Spinner({ size = 'md', ariaLabel = 'Loading' }: SpinnerProps) {
  return (
    <div
      className={`spinner spinner-${size}`}
      role="status"
      aria-label={ariaLabel}
      aria-live="polite"
    >
      <div className="spinner-ring" />
      <span className="sr-only">{ariaLabel}</span>
    </div>
  );
}