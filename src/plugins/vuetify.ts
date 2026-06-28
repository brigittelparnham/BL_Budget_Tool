import { createVuetify } from "vuetify";
import "@mdi/font/css/materialdesignicons.css";
import "vuetify/styles";

const brainlabsLight = {
  dark: false,
  colors: {
    background: "#EEF1EC",
    surface: "#FFFFFF",
    "surface-bright": "#FCFDFB",
    primary: "#6B4DE6",
    secondary: "#1B211D",
    success: "#14935E",
    warning: "#D89A14",
    "deep-orange": "#E2691F",
    error: "#DC4642",
    "on-surface": "#1B211D",
    "on-background": "#1B211D",
    "on-primary": "#FFFFFF",
  },
};

export default createVuetify({
  theme: {
    defaultTheme: "brainlabsLight",
    themes: { brainlabsLight },
  },
  defaults: {
    VCard: { rounded: "0", elevation: 0, border: true },
    VBtn: { rounded: "lg" },
    VChip: { rounded: "pill" },
    VTextField: { color: "primary" },
  },
});
