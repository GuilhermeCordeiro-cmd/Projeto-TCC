// Validação de formulário e Integração Firebase + Flask
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault(); // 1. Bloqueia o recarregamento padrão da página

        const emailInput = document.querySelector('#email'); // Captura o input de email
        const emailValue = emailInput.value;
        const passwordValue = passwordInput.value;

        // Validação visual da senha
        if (passwordValue.length < 8) {
            passError.style.display = 'block';
            passwordInput.style.borderColor = 'var(--error)';
            
            passwordInput.animate([
                { transform: 'translateX(0px)' },
                { transform: 'translateX(5px)' },
                { transform: 'translateX(-5px)' },
                { transform: 'translateX(0px)' }
            ], { duration: 200 });
            return; // Para a execução aqui se a senha for curta
        } else {
            passError.style.display = 'none';
            passwordInput.style.borderColor = 'var(--primary)';
        }

        // 2. CHAMADA AO FIREBASE (Autenticação do Google)
        firebase.auth().signInWithEmailAndPassword(emailValue, passwordValue)
            .then((userCredential) => {
                const user = userCredential.user;

                // 3. PONTE COM O FLASK: Envia o UID do Firebase para salvar no trituno.db
                return fetch('/api/salvar-usuario-firebase', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        uid: user.uid,
                        email: user.email,
                        nome: user.displayName || "Músico Aprendiz"
                    })
                });
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === "sucesso") {
                    console.log("Sincronizado com o trituno.db!");
                    // 4. REDIRECIONAMENTO REAL: Agora sim vai para a página de lições!
                    window.location.href = "/licoes";
                } else {
                    alert("Erro na sincronização do banco local: " + data.mensagem);
                }
            })
            .catch((error) => {
                console.error("Erro na autenticação:", error.message);
                alert("Falha no login: Verifique suas credenciais no Firebase.");
            });
    });