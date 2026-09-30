const dialog=document.getElementById('viewer');
const buttons=Array.from(document.querySelectorAll('.image-button'));
let current=0;
function show(index){current=(index+buttons.length)%buttons.length;const button=buttons[current];document.getElementById('viewer-image').src=button.dataset.src;document.getElementById('viewer-image').alt=button.dataset.caption;document.getElementById('viewer-caption').textContent=button.dataset.caption;document.getElementById('position').textContent=`${current+1} / ${buttons.length}`;}
buttons.forEach((button,index)=>button.addEventListener('click',()=>{show(index);dialog.showModal();document.body.style.overflow='hidden';}));
document.getElementById('close').addEventListener('click',()=>dialog.close());
dialog.addEventListener('close',()=>{document.body.style.overflow='';});
document.getElementById('previous').addEventListener('click',()=>show(current-1));
document.getElementById('next').addEventListener('click',()=>show(current+1));
dialog.addEventListener('keydown',event=>{if(event.key==='ArrowLeft')show(current-1);if(event.key==='ArrowRight')show(current+1);});
