const generateDerivatedBtn = document.getElementById('generate-derivated-btn'); //El botón que va a inicializar el proceso de generación de forms para el formset de skus derivados.
const derivatedCountInput = document.getElementById('derivated-count-input'); //El input cuyo valor interno va a definir la cantidad de forms para el formset de skus derivados.
const derivatedContainer = document.getElementById('derivated-formset-container'); //El div que contendrá los forms del formset de skus derivados.


function renumberDerivatedRows() {
    const rows = derivatedContainer.querySelectorAll('p');
    rows.forEach((row, i) => {
        row.querySelector('label').setAttribute('for', `id_derivated-${i}-sku`);
        row.querySelector('label').textContent = `SKU derivado ${i + 1}:`;
        const input = row.querySelector('input');
        input.name = `derivated-${i}-sku`;
        input.id = `id_derivated-${i}-sku`;
    });
    document.getElementById('id_derivated-TOTAL_FORMS').value = rows.length;    
}


generateDerivatedBtn.addEventListener('click', () => { //Si es que se hace click al botón de id 'generate-derivated-btn'.
    const n = parseInt(derivatedCountInput.value); //n --> Tenrá el valor entero del input puesto en el elemento derivatedCountInput
    if (isNaN(n) || n < 0) return; //Sí n no es un número (NaN -> Not a Number)o n es menor a 0, entonce se va a hacer un return. El evento del click llegará hasta aquí.

    if (n == 0){ //Sí n es 0.
        derivatedContainer.innerHTML = ''; //Se va a dejar vacío el contenido html interno de derivatedContainer. Esto va a borrar los forms de sku derivados si es que habían.
        return; //El evento del click llegará hasta aquí.
    }

    for (let i = 0; i < n; i++) { //Se va a recorrer 'n'. Este for se usará para agregar o eliminar forms del formset de skus derivados

        if (derivatedContainer.children[i] !== undefined){ //En el caso de que exista un form de sku derivado en el índice 'i' del objeto padre 'derivatedContainer'
            continue; //Se va a continuar al siguiente índice del for.
        }

        const p = document.createElement('p'); //Se va a crear un elemento <p> que es lo que va a contener los componentes de un form de sku derivado.
        p.innerHTML = `
            <label for="id_derivated-${i}-sku">SKU derivado ${i + 1}:</label>
            <input type="text" name="derivated-${i}-sku" id="id_derivated-${i}-sku" maxlength="100">
            <i class="remove-derivated" style="color:red; font-style: normal; cursor: pointer;">&#10006;</i>
        `; //A este elemento <p> se agregará un <label>, un <input> y un <i> con una X que va a servír como botón para eliminar un form de sku derivado.

        p.querySelector('.remove-derivated').addEventListener('click', () => { //Al simbolo X creado anteriormente, se la va a agregar un eventListener que esencialmente va a eliminar el form asociado de sku derivado y va a hacer un recuento general para todos los forms del formset.
            p.remove();
            renumberDerivatedRows();
        });

        derivatedContainer.appendChild(p); //Finalmente se agregá este nuevo form al div padré junto a los otros forms.
    }

    //En el caso de que la cantidad definida en 'n' sea inferior a la cantidad actual de estos forms dentro de derivatedContainer, entonces se van a eliminar los últimos elementos uno por uno hasta que el length de 'derivatedContainer' sea igual a 'n'.
    while (derivatedContainer.children.length > n) {
        derivatedContainer.removeChild(derivatedContainer.lastElementChild);
    }

    document.getElementById('id_derivated-TOTAL_FORMS').value = n;
});
