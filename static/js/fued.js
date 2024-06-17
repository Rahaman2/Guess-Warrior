const answersEl = document.querySelectorAll(".answer-container");
const question = document.getElementById("question");
const answerForm = document.getElementById("answer-form");
const answerInput = document.getElementById("answer-input-field");


/**
 * makes a request to the questions endpoint an object of question and answers or null
 * @returns object || null
 */

const getQuestionData = async () => {
    try {
        
        const response = await fetch("/question");
        const data = await response.json();
        console.log(data.question);
        return data;
    } catch (error) {
     console.error(error);   
     return null;
    }

    }




/*
 * Displays the question
* returns the question object
 */

const displayQuestion = async () => {
    const questionData = await getQuestionData();
    question.textContent =  questionData.question;
    return questionData;
}
/**
 * Displays the appropriate information from the question to the user.
 * It displays the question to the user and displays the answer when
 * a user correctly answers a question.
 */
const storeValuesInElements = async () => {
    const questionData = await displayQuestion(); // wait for the question to be displayed

    answerForm.addEventListener("submit", (e) => {
        e.preventDefault(); // prevent page reloading
        const userAnswer = answerInput.value;
        const answerObj = {
            questionData,
            userAnswer
        }
        sendAnswer(answerObj)
        answerInput.value = "";
    })

    const answer = Object.keys(questionData.answers)
    console.log(answer);
    answersEl.forEach( (answerEl, ind) => {

    });
}

storeValuesInElements();

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

        revealAnswer( response.userAnswer , sorted_answer_list, answers );
        
    } catch (error) {
        console.log(error);
    }
}

/**
 * @param
 */
const isAnswerValid = (userAnswer, validAnswersList) =>  validAnswersList.includes(userAnswer) ? true : false;



const revealAnswer = async ( userAnswer, validAnswersList, validAnswersObject ) => {

    const answers = document.querySelectorAll(".answer");
    const points = document.querySelectorAll(".points");
    console.log(validAnswersList);
    console.log(userAnswer)
    console.log(validAnswersObject)
    if (isAnswerValid(userAnswer,  validAnswersList)) {
        const audio = new Audio("static/assets/correct.mp3");
        await audio.play();
        const elementInd = validAnswersList.indexOf(userAnswer);
        const correctAnswerEL = answers[elementInd] // selecting the correct element to reveal the answer
        const correctPointsEL = points[elementInd] // selecting the correct element to reveal the points for  the answer
        correctAnswerEL.textContent = userAnswer;
        correctPointsEL.textContent =  validAnswersObject[userAnswer];
    } else {
        const audio = new Audio("static/assets/x.mp3")
        audio.play();
    }

}

