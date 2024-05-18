const answers = document.querySelectorAll(".answer-container");
const question = document.getElementById("question");




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

    
    const storeValuesInElements = async () => {
    const questionData = await getQuestionData();
    question.textContent =  questionData.question;
    
    
    answers.forEach( (answerEl, ind) => {
        const answerField = answerEl.firstChild;
        const pointsField = answerEl.nextSibling.nextSibling;
        console.log(answerField.classList, pointsField.classList)
        const hidden = answerField.classList;
        if(hidden) {
            answerField.textContent = questionData.sorted_answer_list[ind];
        }
    });
}

storeValuesInElements();

