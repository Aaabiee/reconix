import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/**/*.{ts,tsx}',
    './App.tsx',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#e8f4fa', 100: '#c5e3f2', 200: '#9fd0e9', 300: '#78bde0',
          400: '#3a9ac7', 500: '#065A82', 600: '#054d6e', 700: '#044059',
          800: '#033344', 900: '#022630',
        },
        secondary: {
          50: '#eaf5f9', 100: '#c9e6f0', 200: '#a5d5e6', 300: '#80c4dc',
          400: '#4ea8ca', 500: '#1C7293', 600: '#17607c', 700: '#124e65',
          800: '#0d3c4e', 900: '#082a37',
        },
        accent: {
          50: '#e6fbf4', 100: '#b3f3e0', 200: '#80ebcc', 300: '#4de3b8',
          400: '#26dba8', 500: '#02C39A', 600: '#02a883', 700: '#018d6d',
          800: '#017257', 900: '#005741',
        },
        success: { 50: '#f0fdf4', 500: '#059669', 600: '#047857' },
        warning: { 50: '#fffbeb', 500: '#D97706', 600: '#b45309' },
        error: { 50: '#fef2f2', 500: '#DC2626', 600: '#b91c1c' },
        surface: { DEFAULT: '#FFFFFF', 50: '#FAFBFC', 100: '#F1F5F9', 200: '#E2E8F0' },
      },
      backgroundColor: { page: '#F0F4F8', surface: { DEFAULT: '#FFFFFF', 50: '#FAFBFC', 100: '#F1F5F9', 200: '#E2E8F0' } },
      textColor: { default: '#1a2332', muted: '#64748b' },
      fontFamily: { sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'] },
      boxShadow: {
        'elevation-1': '0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)',
        'elevation-2': '0 3px 6px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06)',
        'elevation-3': '0 10px 20px rgba(0,0,0,0.1), 0 3px 6px rgba(0,0,0,0.06)',
        'elevation-4': '0 14px 28px rgba(0,0,0,0.12), 0 10px 10px rgba(0,0,0,0.06)',
        'elevation-5': '0 19px 38px rgba(0,0,0,0.15), 0 15px 12px rgba(0,0,0,0.08)',
        'inner-glow': 'inset 0 1px 2px rgba(6,90,130,0.08)',
      },
      borderRadius: {
        'material-sm': '4px', 'material': '8px', 'material-md': '12px',
        'material-lg': '16px', 'material-xl': '24px',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(20px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        slideDown: { '0%': { opacity: '0', transform: 'translateY(-10px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        scaleIn: { '0%': { opacity: '0', transform: 'scale(0.92)' }, '100%': { opacity: '1', transform: 'scale(1)' } },
        shimmer: { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out', 'slide-up': 'slideUp 0.5s ease-out',
        'slide-down': 'slideDown 0.3s ease-out', 'scale-in': 'scaleIn 0.3s ease-out',
        'shimmer': 'shimmer 1.5s infinite',
      },
    },
  },
  plugins: [],
};

export default config;
