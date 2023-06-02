const comments = document.querySelectorAll('.comments');
const commentsButton = document.querySelectorAll('#commentsButton');

commentsButton.forEach((commentButton, index) => {
    commentButton.addEventListener('click', () => {
        const targetComment = comments[index];
        targetComment.classList.toggle('active');
    });
});
