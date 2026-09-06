document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('.model-card').forEach(card=>{
    const ta=card.querySelector('.model-text'),count=card.querySelector('.char-count'),file=card.querySelector('.file-input'),label=card.querySelector('.file-label');
    const update=()=>{if(count&&ta)count.textContent=(ta.value||'').replace(/\s/g,'').length+' 字'};
    if(ta){ta.addEventListener('input',update);update()}
    if(file&&label){file.addEventListener('change',()=>{if(file.files&&file.files[0])label.childNodes[0].nodeValue='已选择：'+file.files[0].name+' '})}
  });
  const printBtn=document.getElementById('print-page');
  if(printBtn)printBtn.addEventListener('click',()=>window.print());
});
