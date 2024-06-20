"use strict";

// element selectors
var answerContainers = document.querySelectorAll(".answer-container");
var number = document.querySelectorAll(".number");
var form = document.querySelector("form"); //  TESTING OUT THE FLIP ANIMATION, CODE TO BE ADJUSTED TO ONLY FLIP WHEN THE RESPONSES FROM THE API ARRIVE
// answerContainers.forEach( answerContainer => {
//       answerContainer.addEventListener("mouseover", (event) => {
//             const elemenToFlip = event.target;
//             flipElement(elemenToFlip);
//         })
// })
// answerContainers.forEach( answerContainer => {
//       answerContainer.addEventListener("onmouseout", (event) => {
//             const elementToRestore = event.target;
//             flipElement(elementToRestore);
//         });
//     })
// animations flipper

function flipElement(element) {
  element.classList.toggle('flipped');
}

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
          console.log(data);
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
}; // console.log(questionObject);


var displayQuestion = function displayQuestion() {
  var questionObject, timerInterval;
  return regeneratorRuntime.async(function displayQuestion$(_context2) {
    while (1) {
      switch (_context2.prev = _context2.next) {
        case 0:
          _context2.next = 2;
          return regeneratorRuntime.awrap(getQuestionData());

        case 2:
          questionObject = _context2.sent;
          Swal.fire({
            //   title: "Auto close alert!",
            title: questionObject.question,
            html: "Time left <b></b> seconds.",
            position: "top-start",
            toast: true,
            showConfirmButton: false,
            timer: 60000,
            timerProgressBar: true,
            background: "#DEEEFF",
            didOpen: function didOpen() {
              // Swal.showLoading();
              var timer = Swal.getPopup().querySelector("b");
              timerInterval = setInterval(function () {
                timer.textContent = "".concat(Math.floor(Swal.getTimerLeft() / 1000));
              }, 1000);
            },
            willClose: function willClose() {
              clearInterval(timerInterval);
            }
          }).then(function (result) {
            /* Read more about handling dismissals below */
            if (result.dismiss === Swal.DismissReason.timer) {
              console.log("I was closed by the timer");
            }
          });
          return _context2.abrupt("return", questionObject);

        case 5:
        case "end":
          return _context2.stop();
      }
    }
  });
};

var sendAnswer = function sendAnswer(answer) {
  var data, json, response, _response$questionDat, sorted_answer_list, answers, _userAnswer;

  return regeneratorRuntime.async(function sendAnswer$(_context3) {
    while (1) {
      switch (_context3.prev = _context3.next) {
        case 0:
          data = answer; // console.log(data)

          _context3.prev = 1;
          _context3.next = 4;
          return regeneratorRuntime.awrap(fetch("/question", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
          }));

        case 4:
          json = _context3.sent;
          _context3.next = 7;
          return regeneratorRuntime.awrap(json.json());

        case 7:
          response = _context3.sent;
          console.log(response);
          _response$questionDat = response.questionData, sorted_answer_list = _response$questionDat.sorted_answer_list, answers = _response$questionDat.answers, _userAnswer = _response$questionDat.userAnswer;
          console.log("The user answer is " + response.userAnswer); // revealAnswer( response.userAnswer , sorted_answer_list, answers );

          return _context3.abrupt("return", response);

        case 14:
          _context3.prev = 14;
          _context3.t0 = _context3["catch"](1);
          console.log(_context3.t0);

        case 17:
        case "end":
          return _context3.stop();
      }
    }
  }, null, null, [[1, 14]]);
};

var revealAnswer = function revealAnswer(userAnswer, sorted_answer_list, answers) {
  var answersTextContainer = document.querySelectorAll(".answer"); // where answers will be displayed

  var answerPosition = document.querySelectorAll(".number");
  var points = document.querySelector('.player-points');

  if (validAnswer(userAnswer, sorted_answer_list)) {
    var pointsDisplayer = points.firstElementChild;
    var currentPoints = parseInt(pointsDisplayer.textContent);
    pointsDisplayer.textContent = parseInt(currentPoints) + parseInt(answers[userAnswer]);
    var answerIndex = sorted_answer_list.indexOf(userAnswer);
    var elementToFlip = answerContainers[answerIndex];
    var answerDisplayer = answersTextContainer[answerIndex];
    answerPosition[answerIndex].textContent = answers[userAnswer];
    flipElement(elementToFlip);
    answerDisplayer.textContent = userAnswer;
    playSound(true);
  } else {
    playSound(false);
  }
};

var validAnswer = function validAnswer(userAnswer, sorted_answer_list) {
  return sorted_answer_list.includes(userAnswer);
};

var playSound = function playSound(isCorrect) {
  var audio = isCorrect ? new Audio("static/assets/correct.mp3") : new Audio("static/assets/x.mp3");
  audio.play();
};
/**
 * 
 * @param {*questionObject} questionData 
 * {
    "answers": {question: points},
    "question",
    "sorted_answer_list": []
    }
  * @returns {*questionObject} with the users analized answer.
 */


var handleAnswerSubmission = function handleAnswerSubmission(questionData) {
  return new Promise(function (resolve) {
    form.addEventListener('submit', function _callee(event) {
      var input, answerObj, response;
      return regeneratorRuntime.async(function _callee$(_context4) {
        while (1) {
          switch (_context4.prev = _context4.next) {
            case 0:
              event.preventDefault();
              input = document.querySelector("input");
              userAnswer = input.value;
              answerObj = {
                questionData: questionData,
                userAnswer: userAnswer
              };
              console.log(answerObj);
              _context4.next = 7;
              return regeneratorRuntime.awrap(sendAnswer(answerObj));

            case 7:
              response = _context4.sent;
              input.value = "";
              resolve(response);

            case 10:
            case "end":
              return _context4.stop();
          }
        }
      });
    });
  });
}; // an immediately invoked function explression


var runGame = function _callee2() {
  var questionData, responseObject, _userAnswer2, _ref, sorted_answer_list, answers;

  return regeneratorRuntime.async(function _callee2$(_context5) {
    while (1) {
      switch (_context5.prev = _context5.next) {
        case 0:
          _context5.next = 2;
          return regeneratorRuntime.awrap(displayQuestion());

        case 2:
          questionData = _context5.sent;

        case 3:
          if (!true) {
            _context5.next = 18;
            break;
          }

          _context5.next = 6;
          return regeneratorRuntime.awrap(handleAnswerSubmission(questionData));

        case 6:
          responseObject = _context5.sent;
          console.log(responseObject);
          _userAnswer2 = responseObject.userAnswer;
          _context5.next = 11;
          return regeneratorRuntime.awrap(responseObject.questionData);

        case 11:
          _ref = _context5.sent;
          sorted_answer_list = _ref.sorted_answer_list;
          answers = _ref.answers;
          _context5.next = 16;
          return regeneratorRuntime.awrap(revealAnswer(_userAnswer2, sorted_answer_list, answers));

        case 16:
          _context5.next = 3;
          break;

        case 18:
        case "end":
          return _context5.stop();
      }
    }
  });
}();