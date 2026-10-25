const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const esc=t=>String(t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let tok=localStorage.getItem('brtoken');if(!tok){tok=(crypto.randomUUID?crypto.randomUUID():Date.now()+'-'+Math.random().toString(16).slice(2)).replace(/[^A-Za-z0-9-]/g,'');localStorage.setItem('brtoken',tok)}
const set=Object.assign({sound:true,calm:false,rounds:10},JSON.parse(localStorage.getItem('brset')||'{}'));
let G=null,lastR=null,nick=localStorage.getItem('brnick')||'';
function toast(m){const t=$('#toast');t.textContent=m;t.style.display='block';setTimeout(()=>t.style.display='none',3500)}
async function api(u,body){try{const r=await fetch(u,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:tok,...body})}:undefined);const d=await r.json();if(!r.ok)throw Error(d.error||'Server error');return d}catch(e){toast('Oops: '+e.message);throw e}}
function beep(f){if(!set.sound)return;try{const a=new (window.AudioContext||webkitAudioContext)(),o=a.createOscillator(),g=a.createGain();o.frequency.value=f;g.gain.value=.08;o.connect(g);g.connect(a.destination);o.start();o.stop(a.currentTime+.15)}catch(e){}}
function applySet(){document.body.classList.toggle('calm',set.calm);$('#sSound').checked=set.sound;$('#sCalm').checked=set.calm;$('#sRounds').value=set.rounds;localStorage.setItem('brset',JSON.stringify(set))}
function panel(id){$$('.panel').forEach(p=>p.hidden=p.id!=='p-'+id)}
function openGame(){if(!$('#game').open)$('#game').showModal();panel(G&&G.live?'round':'onboard');if(!G||!G.live)$('#nick').value=nick}
$$('[data-play]').forEach(b=>b.onclick=openGame);
$$('[data-go]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();const id=a.dataset.go;$('#menu').classList.remove('open');$('#burger').setAttribute('aria-expanded','false');if(id==='play')return openGame();$('#game').close();document.getElementById(id).scrollIntoView({behavior:set.calm?'auto':'smooth'});history.replaceState(null,'','#'+id)}));
$('#burger').onclick=()=>{const o=$('#menu').classList.toggle('open');$('#burger').setAttribute('aria-expanded',o)};
$('#closeGame').onclick=()=>$('#game').close();
$('#gear').onclick=()=>{applySet();$('#settings').showModal()};$('#closeS').onclick=()=>$('#settings').close();
$('#sSound').onchange=e=>{set.sound=e.target.checked;applySet()};$('#sCalm').onchange=e=>{set.calm=e.target.checked;applySet()};$('#sRounds').onchange=e=>{set.rounds=+e.target.value;applySet()};
$('#reset').onclick=async()=>{if(!confirm('Delete ALL your game history and stats? This cannot be undone.'))return;await api('/api/settings/reset',{confirm:true});G=null;toast('History cleared.');loadStats()};
$('#nickForm').onsubmit=e=>{e.preventDefault();nick=$('#nick').value.trim().slice(0,24);localStorage.setItem('brnick',nick);begin()};
async function begin(){try{const d=await api('/api/game/start',{nickname:nick,rounds:set.rounds});G={live:true,sid:d.session_id,rounds:d.rounds};panel('round');show(d,{correct:0,predictions_made:0,accuracy:null})}catch(e){}}
function show(d,score){G.sc=d.scenario;G.round=d.round;G.locked=false;$('#hRound').textContent=`ROUND ${String(d.round).padStart(2,'0')} / ${String(G.rounds).padStart(2,'0')}`;
 $('#hScore').textContent=`MACHINE SCORE: ${score.correct} CORRECT · ACCURACY: ${score.accuracy===null?'--':score.accuracy+'%'}`;$('#bar').style.width=((d.round-1)/G.rounds*100)+'%';
 $('#q').textContent=(d.round===1?"ROUND 01: LET'S LEARN YOUR VIBE. ":'')+d.scenario.text;
 const p=d.prediction,po=p&&d.scenario.options.find(o=>o.id===p.option_id);
 $('#pred').innerHTML=p?`🔮 Professor Noodle guesses: <b>${esc(po.emoji+' '+po.text)}</b><br><small class="mono">${esc(p.source)} guess · heuristic confidence ~${p.confidence}% (not a real probability)</small>`:"🧪 Still learning, so no guess yet. Choose what feels right. Don't overthink it. Unless that's your thing.";
 $('#cards').innerHTML=d.scenario.options.map(o=>`<button class="opt" data-id="${o.id}"><em>${o.emoji}</em>${esc(o.text)}</button>`).join('');
 $$('.opt').forEach(b=>b.onclick=()=>choose(b));$('#react').hidden=true;$('.opt').focus()}
async function choose(b){if(G.locked)return;G.locked=true;$$('.opt').forEach(x=>x.disabled=true);b.classList.add('chosen');
 try{const r=await api('/api/game/answer',{session_id:G.sid,scenario_id:G.sc.id,option_id:b.dataset.id,last_reaction:lastR});lastR=r.reaction;
 if(r.predicted)$$('.opt').forEach(x=>{if(x.dataset.id===r.predicted)x.insertAdjacentHTML('beforeend','<span class="tag">🔮 machine guess</span>')});
 const bx=$('#react');bx.hidden=false;bx.className='react '+(r.kind==='correct'?'ok':r.kind==='wrong'?'bad':'');
 const icon=r.kind==='correct'?'✅ ':r.kind==='wrong'?'❌ ':'🧪 ';$('#rText').textContent=icon+r.reaction;$('#rWhy').textContent=r.explanation;
 $('#bar').style.width=(r.round/r.rounds*100)+'%';$('#hScore').textContent=`MACHINE SCORE: ${r.score.correct} CORRECT · ACCURACY: ${r.score.accuracy===null?'--':r.score.accuracy+'%'}`;
 if(r.kind==='correct'){confetti();beep(660)}else beep(r.kind==='wrong'?200:400);
 const n=$('#next');n.textContent=r.finished?'SEE RESULTS':'NEXT ROUND';n.focus();
 n.onclick=()=>{if(r.finished){G.live=false;results(r.summary)}else show(r.next,r.score)}}catch(e){G.locked=false;$$('.opt').forEach(x=>x.disabled=false);b.classList.remove('chosen')}}
function confetti(){if(set.calm||matchMedia('(prefers-reduced-motion:reduce)').matches)return;for(let i=0;i<22;i++){const s=document.createElement('span');s.className='conf';s.textContent=['⭐','🎉','✨','🟡'][i%4];s.style.left=Math.random()*100+'vw';s.style.animationDelay=Math.random()*.4+'s';$('#game').appendChild(s);setTimeout(()=>s.remove(),2200)}}
function count(el,to){const t=set.calm?1:600,s=performance.now();(function f(n){const k=Math.min(1,(n-s)/t);el.textContent=Math.round(to*k);if(k<1)requestAnimationFrame(f)})(s)}
function results(s){panel('result');const acc=s.accuracy;
 $('#resBox').innerHTML=`<div class="card mint"><h3>${esc(s.title)}</h3><p>${esc(s.text)}</p></div><div class="statGrid"><div class="card cream"><div class="big-n" data-n="${s.rounds}">0</div>rounds played</div><div class="card sky"><div class="big-n" data-n="${s.predictions_made}">0</div>predictions made</div><div class="card mint"><div class="big-n" data-n="${s.correct}">0</div>✅ correct</div><div class="card peach"><div class="big-n" data-n="${s.incorrect}">0</div>❌ incorrect</div></div>
 <p><b>Accuracy:</b> <span class="mono">${acc===null?'Not enough data':acc+'%'}</span> · earlier decisions the engine could learn from: <span class="mono">${s.history_used}</span></p>${s.categories.length?'<p><b>By category:</b> '+s.categories.map(c=>`${esc(c.category)} ${c.correct}/${c.total}`).join(' · ')+'</p>':''}<p class="note">A score only says how this simple counter-based model did. It does not measure how predictable you really are.</p>`;
 $$('[data-n]').forEach(e=>count(e,+e.dataset.n));loadStats()}
$('#again').onclick=()=>{panel('round');begin()};$('#toStats').onclick=()=>{$('#game').close();$('#stats').scrollIntoView()};$('#toHome').onclick=()=>{$('#game').close();$('#home').scrollIntoView()};
async function loadStats(){const box=$('#statsBox');try{const [s,h]=await Promise.all([api('/api/stats?token='+tok),api('/api/history?token='+tok)]);
 if(!s.games){box.innerHTML='<div class="card cream empty"><svg class="noodle sm" viewBox="0 0 200 240"><use href="#noodle"/></svg><h3>YOUR DATA IS CURRENTLY MORE EMPTY THAN PROFESSOR NOODLE\'S LUNCHBOX.</h3><button class="btn coral big" id="firstExp">START YOUR FIRST EXPERIMENT</button></div>';$('#firstExp').onclick=openGame;return}
 const mx=a=>Math.max(1,...a.map(x=>x.count));const bars=a=>a.map(x=>`<div class="hbar"><span class="lbl" style="min-width:110px">${esc(x.name)}</span><i style="width:${x.count/mx(a)*60}%"></i><span class="mono">${x.count}</span></div>`).join('');
 box.innerHTML=`<div class="statGrid"><div class="card coralC" style="transform:rotate(-1deg)"><div class="big-n">${s.games}</div>games played</div><div class="card mint" style="transform:rotate(1.5deg)"><div class="big-n">${s.rounds}</div>rounds answered</div><div class="card grape"><div class="big-n">${s.accuracy===null?'--':s.accuracy+'%'}</div><span title="correct predictions ÷ predictions made">overall accuracy (${s.correct}/${s.made})</span></div></div>
 <div class="statGrid"><div class="card cream"><h3>Most-picked tags</h3>${bars(s.tags)}</div><div class="card sky"><h3>Most-picked option types</h3>${bars(s.keys)}</div><div class="card cream"><h3>Accuracy by recent game</h3><div class="vbars">${h.sessions.slice().reverse().map(x=>`<div style="height:${x.accuracy||0}%" title="${x.correct}/${x.made}"><span class="mono">${x.accuracy===null?'n/a':x.accuracy+'%'}</span></div>`).join('')}</div></div></div>
 <div class="card cream" style="margin-top:18px;overflow-x:auto"><h3>Recent games</h3><table><tr><th>Date</th><th>Rounds</th><th>Guesses</th><th>Correct</th><th>Accuracy</th></tr>${h.sessions.map(x=>`<tr><td>${esc(x.date)}</td><td>${x.rounds}</td><td>${x.made}</td><td>${x.correct}</td><td>${x.accuracy===null?'n/a':x.accuracy+'%'}</td></tr>`).join('')}</table></div>`}catch(e){box.innerHTML='<div class="card cream">Could not load stats. Is the server running?</div>'}}
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)$$('#menu a').forEach(a=>a.classList.toggle('on',a.dataset.go===e.target.id))}),{rootMargin:'-40% 0px -50% 0px'});['home','how','stats','about'].forEach(i=>io.observe(document.getElementById(i)));
applySet();loadStats();
