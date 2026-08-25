export default [
  {
    ignores: [
      ".agents/**",
      ".claude/**",
      "dist/**",
      "node_modules/**",
      "output/**",
      "playwright-report/**",
      "test-results/**",
    ],
  },
  {
    files: ["**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        document: "readonly",
        window: "readonly",
      },
    },
    rules: {
      "no-undef": "error",
      "no-unused-vars": "error",
    },
  },
];
