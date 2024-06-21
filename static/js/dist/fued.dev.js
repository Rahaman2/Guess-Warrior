"use strict";

var answersEl = document.querySelectorAll(".answer-container");
var question = document.getElementById("question");
var answerForm = document.getElementById("answer-form");
var answerInput = document.getElementById("answer-input-field");
/**
 * makes a request to the questions endpoint an object of question and answers or null
 * @returns object || null
 */

var getQuestionData = function getQuestionData() {
  var response, data;
  return regeneratorRuntime.async(function getQuestionData$(_context) {
    while (1) {
      switch (_context.prev = _context.next) {
        case 0:
          _context.prev = 0;
          _context.next = 3;
          return regeneratorRuntime.awrap(fetch("/question"));

        case 3:
          response = _context.sent;
          _context.next = 6;
          return regeneratorRuntime.awrap(response.json());

        case 6:
          data = _context.sent;
          console.log(data.question);
          return _context.abrupt("return", data);

        case 11:
          _context.prev = 11;
          _context.t0 = _context["catch"](0);
          console.error(_context.t0);
          return _context.abrupt("return", null);

        case 15:
        case "end":
          return _context.stop();
      }
    }
  }, null, null, [[0, 11]]);
};
/*
 * Displays the question
* returns the question object
 */


var displayQuestion = function displayQuestion() {
  var questionData;
  return regeneratorRuntime.async(function displayQuestion$(_context2) {
    while (1) {
      switch (_context2.prev = _context2.next) {
        case 0:
          _context2.next = 2;
          return regeneratorRuntime.awrap(getQuestionData());

        case 2:
          questionData = _context2.sent;
          question.textContent = questionData.question;
          return _context2.abrupt("return", questionData);

        case 5:
        case "end":
          return _context2.stop();
      }
    }
  });
};
/**
 * Displays the appropriate information from the question to the user.
 * It displays the question to the user and displays the answer when
 * a user correctly answers a question.
 */


var storeValuesInElements = function storeValuesInElements() {
  var questionData, answer;
  return regeneratorRuntime.async(function storeValuesInElements$(_context3) {
    while (1) {
      switch (_context3.prev = _context3.next) {
        case 0:
          _context3.next = 2;
          return regeneratorRuntime.awrap(displayQuestion());

        case 2:
          questionData = _context3.sent;
          // wait for the question to be displayed
          answerForm.addEventListener("submit", function (e) {
            e.preventDefault(); // prevent page reloading

            var userAnswer = answerInput.value;
            var answerObj = {
              questionData: questionData,
              userAnswer: userAnswer
            };
            sendAnswer(answerObj);
            answerInput.value = "";
          });
          answer = Object.keys(questionData.answers);
          console.log(answer);
          answersEl.forEach(function (answerEl, ind) {});

        case 7:
        case "end":
          return _context3.stop();
      }
    }
  });
};

storeValuesInElements();

var sendAnswer = function sendAnswer(answer) {
  var data, json, response, _response$questionDat, sorted_answer_list, answers, userAnswer;

  return regeneratorRuntime.async(function sendAnswer$(_context4) {
    while (1) {
      switch (_context4.prev = _context4.next) {
        case 0:
          data = answer;
          console.log(data);
          _context4.prev = 2;
          _context4.next = 5;
          return regeneratorRuntime.awrap(fetch("/question", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
          }));

        case 5:
          json = _context4.sent;
          _context4.next = 8;
          return regeneratorRuntime.awrap(json.json());

        case 8:
          response = _context4.sent;
          console.log(response);
          _response$questionDat = response.questionData, sorted_answer_list = _response$questionDat.sorted_answer_list, answers = _response$questionDat.answers, userAnswer = _response$questionDat.userAnswer;
          console.log("The user answer is " + response.userAnswer);
          revealAnswer(response.userAnswer, sorted_answer_list, answers);
          _context4.next = 18;
          break;

        case 15:
          _context4.prev = 15;
          _context4.t0 = _context4["catch"](2);
          console.log(_context4.t0);

        case 18:
        case "end":
          return _context4.stop();
      }
    }
  }, null, null, [[2, 15]]);
};
/**
 * @param
 */


var isAnswerValid = function isAnswerValid(userAnswer, validAnswersList) {
  return validAnswersList.includes(userAnswer) ? true : false;
};

var revealAnswer = function revealAnswer(userAnswer, validAnswersList, validAnswersObject) {
  var answers, points, audio, elementInd, correctAnswerEL, correctPointsEL, _audio;

  return regeneratorRuntime.async(function revealAnswer$(_context5) {
    while (1) {
      switch (_context5.prev = _context5.next) {
        case 0:
          answers = document.querySelectorAll(".answer");
          points = document.querySelectorAll(".points");
          console.log(validAnswersList);
          console.log(userAnswer);
          console.log(validAnswersObject);

          if (!isAnswerValid(userAnswer, validAnswersList)) {
            _context5.next = 16;
            break;
          }

          audio = new Audio("static/assets/correct.mp3");
          _context5.next = 9;
          return regeneratorRuntime.awrap(audio.play());

        case 9:
          elementInd = validAnswersList.indexOf(userAnswer);
          correctAnswerEL = answers[elementInd]; // selecting the correct element to reveal the answer

          correctPointsEL = points[elementInd]; // selecting the correct element to reveal the points for  the answer

          correctAnswerEL.textContent = userAnswer;
          correctPointsEL.textContent = validAnswersObject[userAnswer];
          _context5.next = 18;
          break;

        case 16:
          _audio = new Audio("static/assets/x.mp3");

          _audio.play();

        case 18:
        case "end":
          return _context5.stop();
      }
    }
  });
};