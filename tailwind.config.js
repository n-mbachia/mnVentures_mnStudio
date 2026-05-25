/** @type {import('tailwindcss').Config} */
module.exports = {
  // ── Content paths ──────────────────────────────────────────────────────────
  // Tailwind scans these files and includes ONLY the classes that appear in them.
  // Add any new template directories or JS files here.
  content: [
    './store/templates/**/*.html',
    './templates/**/*.html',
    './static/src/**/*.js',
    // If you later add a JS framework or component files:
    // './static/src/components/**/*.{js,jsx}',
  ],

  // ── Theme ──────────────────────────────────────────────────────────────────
  theme: {
    extend: {
      // Brand colours
      colors: {
        brand: {
          50:      '#fffbeb',
          100:     '#fef3c7',
          200:     '#fde68a',
          300:     '#fcd34d',
          400:     '#fbbf24',
          DEFAULT: '#C28840',   // amber-600 — primary buttons, highlights
          600:     '#b45309',   // Needed for .btn-primary:hover
          700:	   '#92400e',   // Needed for ::-webkit-scrollbar-thumb
          800:     '#78350f',
          900:     '#451a03',
        },
        surface: {
          DEFAULT: '#1c1917',   // stone-900 — card backgrounds
          2:       '#292524',   // stone-800 — inputs, secondary surfaces
          3:       '#44403c',   // stone-700 — borders, dividers
        },
        background: '#0c0a09',  // stone-950 — page background
      },

      // Typography
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'Cambria', 'serif'],
        sans:  ['"DM Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono:  ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },

      // Font sizes
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '1rem' }],
      },

      // Spacing extras
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '88': '22rem',
        '128': '32rem',
      },

      // Border radius
      borderRadius: {
        '4xl': '2rem',
      },

      // Box shadows
      boxShadow: {
        'brand':    '0 4px 30px rgba(180, 83, 9, 0.25)',
        'brand-lg': '0 12px 50px rgba(180, 83, 9, 0.35)',
        'card':     '0 2px 20px rgba(0, 0, 0, 0.4)',
        'card-hover': '0 20px 60px rgba(0, 0, 0, 0.5)',
      },

      // Animations
      keyframes: {
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%':   { opacity: '0', transform: 'translateX(-16px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulse_slow: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.4' },
        },
        countdown_pulse: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%':      { transform: 'scale(1.04)' },
        },
      },
      animation: {
        'fade-up':         'fadeUp 0.6s ease both',
        'fade-up-slow':    'fadeUp 0.8s ease both',
        'fade-in':         'fadeIn 0.4s ease both',
        'slide-in':        'slideIn 0.5s ease both',
        'pulse-slow':      'pulse_slow 2.5s ease-in-out infinite',
        'countdown-pulse': 'countdown_pulse 1s ease-in-out infinite',
      },

      // Transition durations
      transitionDuration: {
        '400': '400ms',
      },

      // Background image helpers
      backgroundImage: {
        'hero-grid':
          'linear-gradient(rgba(217,119,6,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(217,119,6,0.04) 1px, transparent 1px)',
        'brand-gradient':
          'linear-gradient(135deg, #b45309 0%, #78350f 100%)',
        'dark-gradient':
          'linear-gradient(to bottom right, #1c1917, #0c0a09)',
      },
      backgroundSize: {
        'grid-60': '60px 60px',
      },

      // Max width extras
      maxWidth: {
        '8xl': '88rem',
        '9xl': '96rem',
      },
    },
  },

  // ── Plugins ────────────────────────────────────────────────────────────────
  plugins: [
    require('@tailwindcss/forms')({
      // Use the 'class' strategy so form styles only apply where you add the class
      strategy: 'class',
    }),
    require('@tailwindcss/typography'),
  ],
};
