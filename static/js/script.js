// element selectors
const answerContainers = document.querySelectorAll(".answer-container");
const number = document.querySelectorAll(".number");
const form = document.querySelector("form");


//  TESTING OUT THE FLIP ANIMATION, CODE TO BE ADJUSTED TO ONLY FLIP WHEN THE RESPONSES FROM THE API ARRIVE
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
    
    
    


    
const getQuestionData = async () => {
  try {
      
      const response = await fetch("/question");
      const data = await response.json();
      console.log(data);
      return data;
  } catch (error) {
    console.error(error);   
   return null;
  }

}


// console.log(questionObject);

const displayQuestion = async () => {
  const questionObject = await getQuestionData();
  
  let timerInterval;
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
      didOpen: () => {
        // Swal.showLoading();
        const timer = Swal.getPopup().querySelector("b");
        timerInterval = setInterval(() => {
          timer.textContent = `${Math.floor( Swal.getTimerLeft() / 1000)}`;
        }, 1000);
      },
      willClose: () => {
        clearInterval(timerInterval);
      }
    }).then((result) => {
      /* Read more about handling dismissals below */
      if (result.dismiss === Swal.DismissReason.timer) {
        console.log("I was closed by the timer");
      }
    });
    
    return questionObject;
  }



const sendAnswer = async (answer) => {
  const data = answer;
  // console.log(data)
  try {
      const json = await fetch("/question", {
          method: "POST",
          headers: {
              "Content-Type": "application/json"
          }, 
          body: JSON.stringify(data)
      });
  
      const response = await json.json();
      console.log(response);
      const {sorted_answer_list, answers, userAnswer } = response.questionData;

      console.log("The user answer is " +response.userAnswer)

      // revealAnswer( response.userAnswer , sorted_answer_list, answers );
      return response
  } catch (error) {
      console.log(error);
  }
}

const revealAnswer = (userAnswer, sorted_answer_list, answers) => {

  const answersTextContainer = document.querySelectorAll(".answer"); // where answers will be displayed
  const answerPosition = document.querySelectorAll(".number");
  const points = document.querySelector('.player-points');
  if (validAnswer( userAnswer, sorted_answer_list)) {
      const pointsDisplayer = points.firstElementChild
      let currentPoints = parseInt(pointsDisplayer.textContent);
      pointsDisplayer.textContent = parseInt(currentPoints) + parseInt(answers[userAnswer])
      const answerIndex = sorted_answer_list.indexOf( userAnswer );
      const elementToFlip = answerContainers[answerIndex];
      const answerDisplayer = answersTextContainer[answerIndex]
      answerPosition[answerIndex].textContent = answers[userAnswer];

      flipElement(elementToFlip);
      answerDisplayer.textContent = userAnswer
      playSound(true);
  } else {

    playSound(false);
  }

}

const validAnswer = ( userAnswer, sorted_answer_list) => {
 return sorted_answer_list.includes(userAnswer);
}

const playSound = (isCorrect) => {
  const audio = isCorrect ? new Audio("static/assets/correct.mp3") : new Audio("static/assets/x.mp3");
  audio.play();
}

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
const handleAnswerSubmission = (questionData) => {
  return new Promise((resolve) => {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const input = document.querySelector("input");
      userAnswer = input.value;
      const answerObj = { questionData, userAnswer }
      console.log(answerObj);
      const response = await sendAnswer(answerObj);
      input.value = "";
      resolve(response);
    });
  });
}



 // an immediately invoked function explression
const runGame = (async () => {
    
    const questionData = await displayQuestion();
    while (true) {

      const responseObject = await handleAnswerSubmission(questionData);
      console.log(responseObject);
      const userAnswer = responseObject.userAnswer;
      const { sorted_answer_list, answers} = await responseObject.questionData;
      await revealAnswer( userAnswer, sorted_answer_list, answers);
    }
  

})();