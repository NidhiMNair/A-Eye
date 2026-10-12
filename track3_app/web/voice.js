
window.speakAssistance = function (message) {
  if (!("speechSynthesis" in window)) {
    alert("Voice output is not supported in this browser.");
    return;
  }

  window.speechSynthesis.cancel();

  const speech = new SpeechSynthesisUtterance(message);
  speech.lang = "en-US";
  speech.rate = 0.9;
  speech.pitch = 1.0;

  speech.onstart = function () {
    console.log("Voice output started.");
  };

  speech.onerror = function (event) {
    console.error("Speech error:", event.error);
  };

  window.speechSynthesis.speak(speech);
};
