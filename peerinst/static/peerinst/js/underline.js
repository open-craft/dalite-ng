function underlines() {
  'use strict';

  // Decorate h1 headers
  let lines = d3.selectAll(".underline");
  lines.selectAll("g").remove();
  let w = document.querySelector("main").offsetWidth;

  let gradientX = lines.append("linearGradient")
  .attr("id",'underlineGradientX')
  .attr('x1',0)
  .attr('x2',1)
  .attr('y1',0)
  .attr('y2',0);

  gradientX.append("stop")
  .attr("offset",'0%')
  .attr('stop-color','var(--mdc-theme-primary)');

  gradientX.append("stop")
  .attr("offset",'100%')
  .attr('stop-color','var(--mdc-theme-secondary)');

  let gradientY = lines.append("linearGradient")
  .attr("id",'underlineGradientY')
  .attr('x1',0)
  .attr('x2',0)
  .attr('y1',0)
  .attr('y2',1);

  gradientY.append("stop")
  .attr("offset",'0%')
  .attr('stop-color','var(--mdc-theme-secondary)');

  gradientY.append("stop")
  .attr("offset",'100%')
  .attr('stop-color','var(--mdc-theme-primary)');

  let g = lines.append("g");
  g.append("rect")
  .attr("x",-10)
  .attr("y",0)
  .attr("width",w+10)
  .attr("height",1)
  .attr("fill",'url(#underlineGradientX)');

  g.append("rect")
  .attr("x",w)
  .attr("y",0)
  .attr("width",1)
  .attr("height",120)
  .attr("fill",'url(#underlineGradientY)');
}
