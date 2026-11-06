// Particle backdrop (particles.js by Vincent Garreau, MIT, vendored in static/vendor).

const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const CONFIG = {
  particles: {
    number: { value: 70, density: { enable: true, value_area: 900 } },
    color: { value: "#74a9ff" },
    shape: { type: "circle" },
    opacity: {
      value: 0.7,
      random: true,
      anim: { enable: true, speed: 1.2, opacity_min: 0.15, sync: false },
    },
    size: { value: 3.2, random: true },
    line_linked: {
      enable: true,
      distance: 150,
      color: "#4a6fa5",
      opacity: 0.5,
      width: 1,
    },
    move: {
      // Motion and the hover effect are the whole point of the backdrop, so both
      // are dropped rather than slowed when the viewer asks for less movement;
      // the particles still render as a static field.
      enable: !REDUCED_MOTION,
      speed: 2.4,
      direction: "none",
      random: true,
      straight: false,
      out_mode: "out",
    },
  },
  interactivity: {
    detect_on: "canvas",
    events: {
      onhover: { enable: !REDUCED_MOTION, mode: "grab" },
      onclick: { enable: false },
      resize: true,
    },
    modes: { grab: { distance: 160, line_linked: { opacity: 0.55 } } },
  },
  retina_detect: true,
};

if (typeof window.particlesJS === "function") {
  window.particlesJS("particles-js", CONFIG);
}
