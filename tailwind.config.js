/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/templates/**/*.html", "./app/static/js/**/*.js"],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: "#082653",
          800: "#0B336B",
          900: "#061C3D",
        },
        brand: {
          DEFAULT: "#087CF5",
          600: "#0668D1",
        },
        accent: {
          DEFAULT: "#10D99A",
          600: "#0BBF86",
          50: "#E8FBF4",
        },
        canvas: "#F5F7FB",
        muted: "#64748B",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(8, 38, 83, 0.05), 0 10px 28px rgba(8, 38, 83, 0.07)",
        header: "0 1px 0 rgba(8, 38, 83, 0.06)",
      },
      maxWidth: {
        shell: "76rem",
      },
      borderRadius: {
        card: "0.875rem",
      },
    },
  },
  plugins: [],
};
