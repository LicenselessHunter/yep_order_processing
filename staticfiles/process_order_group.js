const process_order_group_modalBtn = document.getElementById('process-order-group-modalBtn');
const process_order_group_modal = document.getElementById('process-order-group-modal');
const close_process_order_group_modal = document.getElementById('close-process-order-group-modal')


process_order_group_modalBtn.addEventListener('click', () => {
    process_order_group_modal.style.display = 'flex';
    process_order_group_modal.style.flexDirection = 'column';
    process_order_group_modal.style.alignItems = 'center';
    process_order_group_modal.style.justifyContent = 'center';

});

close_process_order_group_modal.addEventListener('click', () => {
    process_order_group_modal.style.display = 'none';
});