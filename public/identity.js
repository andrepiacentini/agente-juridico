// Identidade visual da tela inicial do chat (T14.1): subtítulo abaixo da imagem do TJSC e crédito abaixo das
// quatro perguntas. O Chainlit 2.12 não tem lugar nativo para esses textos; este script os acrescenta sempre que a
// tela inicial é montada (a cada "Novo chat"), sem tocar em nada que o Chainlit desenha.

const SUBTITLE = "Desafio técnico: Agente de IA para análise de processos";
const CREDIT_PREFIX = "Desenvolvido por André Piacentini (";
const CREDIT_SUFFIX = ") em setembro de 2026";
const CREDIT_LINKS = [
  { label: "site", url: "https://andrepiacentini.com.br" },
  { label: "LinkedIn", url: "https://www.linkedin.com/in/andrepiacentini/" },
];

function link({ label, url }) {
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.textContent = label;
  anchor.target = "_blank";
  anchor.rel = "noopener noreferrer";
  return anchor;
}

function subtitle() {
  const element = document.createElement("p");
  element.className = "tjsc-subtitle";
  element.textContent = SUBTITLE;
  return element;
}

function credit() {
  const element = document.createElement("p");
  element.className = "tjsc-credit";
  element.append(CREDIT_PREFIX, link(CREDIT_LINKS[0]), " · ", link(CREDIT_LINKS[1]), CREDIT_SUFFIX);
  return element;
}

function decorateWelcomeScreen() {
  const screen = document.getElementById("welcome-screen");
  if (!screen) return;
  const logo = screen.querySelector("img.logo");
  if (logo && !screen.querySelector(".tjsc-subtitle")) logo.after(subtitle());
  const starters = screen.querySelector("#starters");
  if (starters && !screen.querySelector(".tjsc-credit")) starters.after(credit());
}

new MutationObserver(decorateWelcomeScreen).observe(document.body, { childList: true, subtree: true });
decorateWelcomeScreen();
