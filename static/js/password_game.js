document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('answer');

    const rules = {
        length: s => s.length >= 8,
        upper: s => /[A-Z]/.test(s),
        month: s => /(january|february|march|april|may|june|july|august|september|october|november|december)/i.test(s),
        digit: s => /\d/.test(s),
        symbol: s => /[!@#$%^&*()]/.test(s),
        repeat: s => !/(.)\1\1/.test(s),
        sum25: s => [...s].filter(c => /\d/.test(c)).map(Number).reduce((a, b) => a + b, 0) === 25,
        roman: s => /[IVXLCDM]/.test(s),
        product35: s => {
            const matches = s.match(/[IVXLCDM]{1,}/g); // all Roman substrings
            if (!matches) return false;

            const values = matches.map(romanToInt);
            const product = values.reduce((a, b) => a * b, 1);
            return product === 35;
        }


    };

    let allPassed = false;

    input.addEventListener('input', () => {
        const val = input.value;
        const ruleKeys = Object.keys(rules);
        let unlocked = true;

        for (let i = 0; i < ruleKeys.length; i++) {
            const rule = ruleKeys[i];
            const check = rules[rule];
            const item = document.querySelector(`[data-rule="${rule}"]`);

            if (!item) continue;

            if (unlocked) {
                item.style.display = 'list-item';
                const passed = check(val);

                if (passed) {
                    item.classList.add('passed');
                    item.classList.remove('failed');
                    item.textContent = '✅ ' + item.textContent.slice(2);
                    gsap.fromTo(item, { scale: 0.85, opacity: 0.6 }, { scale: 1, opacity: 1, duration: 0.3 });
                } else {
                    item.classList.remove('passed');
                    item.classList.add('failed');
                    item.textContent = '🔴 ' + item.textContent.slice(2);
                    gsap.fromTo(item, { x: -5 }, { x: 5, duration: 0.1, repeat: 3, yoyo: true });
                    unlocked = false;
                }
            } else {
                if (item.classList.contains('passed')) {
                    item.style.display = 'list-item';
                } else {
                    item.style.display = 'none';
                }
            }
        }


        const allPassedNow = ruleKeys.every(rule => rules[rule](val));
        if (allPassedNow && !allPassed) {
            allPassed = true;
            confetti({
                particleCount: 200,
                spread: 60,
                origin: { y: 0.6 }
            });
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1200);
        }

        if (!allPassedNow) {
            allPassed = false;
        }
    });

    function romanToInt(str) {
        const map = { I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000 };
        let total = 0;
        for (let i = 0; i < str.length; i++) {
            const curr = map[str[i]];
            const next = map[str[i + 1]];
            if (next > curr) {
                total += (next - curr);
                i++; // skip next
            } else {
                total += curr;
            }
        }
        return total;
    }
});
