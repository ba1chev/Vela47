// Particle backdrop (particles.js by Vincent Garreau, MIT, vendored in static/vendor).

const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// The library redraws the whole canvas every frame and checks every pair of particles
// for a link, so the cost grows with the square of their number. A fixed count keeps a
// large monitor from multiplying it (with density on, a 1440p screen got about 290),
// and drawing at one pixel per CSS pixel instead of the retina ratio draws a quarter
// of the pixels, which a soft backdrop does not need.
const CONFIG = {
  particles: {
    number: { value: 55, density: { enable: false } },
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
      distance: 140,
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
  retina_detect: false,
};

if (typeof window.particlesJS === "function") {
  window.particlesJS("particles-js", CONFIG);
}
