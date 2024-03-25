function dragEnterHandler(event) {
    event.preventDefault();
    document.getElementById("file-input-container").classList.add('highlight');
}

function dragLeaveHandler(event) {
    event.preventDefault();
    document.getElementById("file-input-container").classList.remove('highlight');
}

function dropHandler(event) {
    event.preventDefault();
    document.getElementById("file-input-container").classList.remove('highlight');

    var file = event.dataTransfer.files[0];
    
    document.getElementById("file-input").files = event.dataTransfer.files;
    
}

function fileInputChangeHandler(event) {
    var file = event.target.files[0];
    console.log('Arquivo selecionado:', file);
}