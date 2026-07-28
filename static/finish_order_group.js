//The change event is fired for <input>, <select>, and <textarea> elements when the user modifies the element's value. En este caso, cuando se cambia el value del <input> de id 'id_manifest_image''


document.getElementById('id_manifest_image').addEventListener('change', function (event) { 
    const file = event.target.files[0]; //event.target.files --> Es un objeto 'FileList', represents an object of this type returned by the files property of the HTML <input> element; this lets you access the list of files selected with the <input type="file">. All <input> element nodes have a files attribute of type FileList on them which allows access to the items in this list. En este caso, se está recogiendo el primer objeto 'files' al acceder al nodo de índice [0], esto es lo que va a contener la imagen subida por el usuario.

    if (!file) return;


    //The FileReader interface lets web applications asynchronously read the contents of files (or raw data buffers) stored on the user's computer, using File or Blob objects to specify the file or data to read. File objects may be obtained from a FileList object returned as a result of a user selecting files using the <input type="file"> element.
    const reader = new FileReader(); //Aqui se inicializa una instancia del lector.

    
    reader.onload = function (e) {
        document.getElementById('manifest-image-preview').src = e.target.result; //Acá se cambia el atributo src del elemento html de id 'manifest-image-preview' por...
    
    };
    reader.readAsDataURL(file);
})
