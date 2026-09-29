document.addEventListener('DOMContentLoaded', () => {
    const inputs = document.querySelectorAll('#regForm input[required], #regForm select[required]');
    const btn = document.getElementById('regBtn');

    function checkReg() {
        let allFilled = true;
        inputs.forEach(input => {
            if (input.value.trim() === "") allFilled = false;
        });
        btn.disabled = !allFilled;
    }

    inputs.forEach(input => {
        input.addEventListener('input', checkReg);
        input.addEventListener('change', checkReg);
    });
});