# PL Radar — proxy ViaggiaTreno (prototipo)

Questo Worker è **solo un test tecnico**, non è ancora pubblicato e non è collegato alla pagina PL Radar. GitHub Pages non esegue codice server.

## Pubblicazione futura
1. Creare un Cloudflare Worker (piano e condizioni da verificare).
2. Inserire il codice di `worker.js` nell'editor del Worker.
3. Configurare `ALLOWED_ORIGIN=https://salvo1984.github.io` come variabile di ambiente.
4. Pubblicare e provare `https://<indirizzo-worker>/api/stations?q=Palma`.
5. Controllare risposta, disponibilità, condizioni d'uso e correttezza dei codici stazione **prima** di collegare l'interfaccia.

Non memorizzare chiavi o credenziali in questo repository. Non usare i risultati per dichiarare aperto/chiuso un passaggio a livello: i treni merci e lo stato delle barriere non sono coperti.

L'endpoint non ufficiale potrebbe non funzionare o impedire richieste automatizzate. In quel caso occorre fermarsi e valutare fonti autorizzate.
