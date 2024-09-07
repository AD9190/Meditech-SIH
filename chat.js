const fs = require('fs');
const readline = require('readline');

// Load intents from JSON file
const intents = JSON.parse(fs.readFileSync('intents.json', 'utf8')).intents;

function preprocessPatterns(intents) {
  return intents.map(intent => ({
    ...intent,
    processedPatterns: intent.patterns.map(pattern => pattern.toLowerCase().split(/\s+/))
  }));
}

function findIntent(userInput, processedIntents) {
  const userWords = userInput.toLowerCase().split(/\s+/);
  let maxOverlap = 0;
  let bestIntent = null;

  for (const intent of processedIntents) {
    for (const pattern of intent.processedPatterns) {
      const overlap = pattern.filter(word => userWords.includes(word)).length;
      if (overlap > maxOverlap) {
        maxOverlap = overlap;
        bestIntent = intent;
      }
    }
  }

  return maxOverlap > 0 ? bestIntent : null;
}

function getResponse(intent) {
  return intent.responses[Math.floor(Math.random() * intent.responses.length)];
}

function chatbot() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  console.log("Chatbot: Hello! How can I assist you today? (Type 'quit' to exit)");

  const processedIntents = preprocessPatterns(intents);

  function chat() {
    rl.question("You: ", (userInput) => {
      if (userInput.toLowerCase() === 'quit') {
        console.log("Chatbot: Goodbye! Have a great day.");
        rl.close();
        return;
      }

      const intent = findIntent(userInput, processedIntents);

      if (intent) {
        const response = getResponse(intent);
        console.log(`Chatbot: ${response}`);
      } else {
        console.log("Chatbot: I'm sorry, I didn't understand that. Could you please rephrase?");
      }

      chat();
    });
  }

  chat();
}

chatbot();