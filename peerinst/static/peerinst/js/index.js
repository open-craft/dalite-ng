// MDC
import autoInit from '@material/auto-init/index';
import * as chips from '@material/chips/index';
import * as dialog from '@material/dialog/index';
import * as iconToggle from '@material/icon-toggle/index';
import * as radio from '@material/radio/index';
import * as ripple from '@material/ripple/index';
import * as textField from '@material/textfield/index';
import * as toolbar from '@material/toolbar/index';

autoInit.register('MDCChip', chips.MDCChip);
autoInit.register('MDCChipSet', chips.MDCChipSet);
autoInit.register('MDCDialog', dialog.MDCDialog);
autoInit.register('MDCIconToggle', iconToggle.MDCIconToggle);
autoInit.register('MDCRadio', radio.MDCRadio);
autoInit.register('MDCRipple', ripple.MDCRipple);
autoInit.register('MDCTextField', textField.MDCTextField);
autoInit.register('MDCToolbar', toolbar.MDCToolbar);

export {
  autoInit,
  chips,
  dialog,
  iconToggle,
  radio,
  ripple,
  textField,
  toolbar,
};


// D3
import * as d3 from 'd3';

export {
  active,
  area,
  axisBottom,
  axisLeft,
  curveNatural,
  entries,
  format,
  interrupt,
  keys,
  line,
  now,
  path,
  range,
  rgb,
  scaleBand,
  scaleLinear,
  scaleOrdinal,
  select,
  selectAll,
  transition,
  values,
} from 'd3';


// Popmotion
import * as pop from 'popmotion';

export {
  pop,
};


// Custom functions
/** Mike Bostock's svg line wrap function
*   https://bl.ocks.org/mbostock/7555321
*   (only slightly modified)
* @function
* @param {String} text
* @param {Int} width
* @this Wrap
*/
export function wrap(text, width) {
  text.each(function() {
    let text = bundle.select(this);
    let words = text.text().split(/\s+/).reverse();
    let word;
    let line = [];
    let lineNumber = 0;
    let lineHeight = 16; // px
    let x = text.attr('x');
    let dx = text.attr('dx');
    let y = text.attr('y');
    let dy = parseFloat(text.attr('dy'));
    let tspan = text.text(null).append('tspan')
      .attr('x', x).attr('y', y).attr('dx', dx).attr('dy', dy + 'px');
    while (word = words.pop()) {
      line.push(word);
      tspan.text(line.join(' '));
      if (tspan.node().getComputedTextLength() > width) {
        line.pop();
        tspan.text(line.join(' '));
        line = [word];
        tspan = text.append('tspan')
          .attr('x', x)
          .attr('y', y)
          .attr('dx', dx)
          .attr('dy', ++lineNumber * lineHeight + dy + 'px').text(word);
      }
    }
  });
}

/** Underline h1 with svg
*  @function
*/
function underlines() {
  'use strict';

  // Decorate h1 headers
  let lines = d3.selectAll('.underline');
  lines.selectAll('g').remove();
  let w = document.querySelector('main').offsetWidth;

  let gradientX = lines.append('linearGradient')
  .attr('id', 'underlineGradientX')
  .attr('x1', 0)
  .attr('x2', 1)
  .attr('y1', 0)
  .attr('y2', 0);

  gradientX.append('stop')
  .attr('offset', '0%')
  .attr('stop-color', 'var(--mdc-theme-primary)');

  gradientX.append('stop')
  .attr('offset', '100%')
  .attr('stop-color', 'var(--mdc-theme-secondary)');

  let gradientY = lines.append('linearGradient')
  .attr('id', 'underlineGradientY')
  .attr('x1', 0)
  .attr('x2', 0)
  .attr('y1', 0)
  .attr('y2', 1);

  gradientY.append('stop')
  .attr('offset', '0%')
  .attr('stop-color', 'var(--mdc-theme-secondary)');

  gradientY.append('stop')
  .attr('offset', '100%')
  .attr('stop-color', 'var(--mdc-theme-primary)');

  let g = lines.append('g');
  g.append('rect')
  .attr('x', -10)
  .attr('y', 0)
  .attr('width', w+10)
  .attr('height', 1)
  .attr('fill', 'url(#underlineGradientX)');

  g.append('rect')
  .attr('x', w)
  .attr('y', 0)
  .attr('width', 1)
  .attr('height', 120)
  .attr('fill', 'url(#underlineGradientY)');
}

/** Question analytics
*  @function
*  @param {Object} matrix
*  @param {Object} freq
*  @param {string} id
*/
export function plot(matrix, freq, id) {
  const colour = {
    'easy': 'rgb(30, 142, 62)',
    'hard': 'rgb(237, 69, 40)',
    'tricky': 'rgb(237, 170, 30)',
    'peer': 'rgb(25, 118, 188)',
  };
  let max = -0;
  let label = '';
  for (let entry in bundle.entries(matrix)) {
    if ({}.hasOwnProperty.call(bundle.entries(matrix), entry)) {
      let item = bundle.entries(matrix)[entry];
      if (item.value > max) {
        max = item.value;
        label = item.key;
      }
    }
  }
  if (max > 0) {
    const rating = document.getElementById('rating-'+id);
    rating.innerHTML=label.substring(0, 1).toUpperCase()+label.substring(1, );

    const stats = document.getElementById('stats-'+id);
    stats.style.color = colour[label];
  }

  const matrixSvg = bundle.select('#matrix-'+id);
  let size = matrixSvg.attr('width');
  const g = matrixSvg.append('g');

  g.append('rect')
  .attr('x', 0)
  .attr('y', 0)
  .attr('width', size/2)
  .attr('height', size/2)
  .attr('fill', colour['easy'])
  .style('opacity', 0.5+0.5*matrix['easy']);

  g.append('text')
  .attr('x', size/4)
  .attr('y', size/4)
  .attr('dy', 4)
  .style('font-size', '8pt')
  .style('fill', 'white')
  .style('text-anchor', 'middle')
  .text(parseInt(100*matrix['easy'])+'%');

  g.append('rect')
  .attr('x', size/2)
  .attr('y', size/2)
  .attr('width', size/2)
  .attr('height', size/2)
  .attr('fill', colour['hard'])
  .style('opacity', 0.5+0.5*matrix['hard']);

  g.append('text')
  .attr('x', 3*size/4)
  .attr('y', 3*size/4)
  .attr('dy', 4)
  .style('font-size', '8pt')
  .style('fill', 'white')
  .style('text-anchor', 'middle')
  .text(parseInt(100*matrix['hard'])+'%');

  g.append('rect')
  .attr('x', 0)
  .attr('y', size/2)
  .attr('width', size/2)
  .attr('height', size/2)
  .attr('fill', colour['peer'])
  .style('opacity', 0.5+0.5*matrix['peer']);

  g.append('text')
  .attr('x', size/4)
  .attr('y', 3*size/4)
  .attr('dy', 4)
  .style('font-size', '8pt')
  .style('fill', 'white')
  .style('text-anchor', 'middle')
  .text(parseInt(100*matrix['peer'])+'%');

  g.append('rect')
  .attr('x', size/2)
  .attr('y', 0)
  .attr('width', size/2)
  .attr('height', size/2)
  .attr('fill', colour['tricky'])
  .style('opacity', 0.5+0.5*matrix['tricky']);

  g.append('text')
  .attr('x', 3*size/4)
  .attr('y', size/4)
  .attr('dy', 4)
  .style('font-size', '8pt')
  .style('fill', 'white')
  .style('text-anchor', 'middle')
  .text(parseInt(100*matrix['tricky'])+'%');

  let firstFreqSvg = bundle.select('#first-frequency-'+id);
  let secondFreqSvg = bundle.select('#second-frequency-'+id);
  let margin = {left: 30, right: 30};

  let sum = 0;
  for (let entry in freq['first_choice']) {
    if ({}.hasOwnProperty.call(freq['first_choice'], entry)) {
      sum += freq['first_choice'][entry];
    }
  }
  for (let entry in freq['first_choice']) {
    if ({}.hasOwnProperty.call(freq['first_choice'], entry)) {
      freq['first_choice'][entry] /= sum;
      freq['second_choice'][entry] /= sum;
    }
  }

  size = (secondFreqSvg.attr('width')-margin.left);

  let x = bundle.scaleLinear().domain([0, 1]).rangeRound([0, size]);
  let y = bundle.scaleBand()
  .domain(bundle.keys(freq['first_choice'])
  .sort()).rangeRound([0, firstFreqSvg.attr('height')]);

  let gg = secondFreqSvg.append('g')
  .attr('transform', 'translate('+margin.left+',0)');

  let ggg = firstFreqSvg.append('g');

  gg.append('g')
  .attr('class', 'axis axis--x')
  .style('opacity', 0)
  .call(bundle.axisBottom(x));

  ggg.append('g')
  .attr('class', 'axis axis--x')
  .style('opacity', 0)
  .call(bundle.axisBottom(x));

  gg.append('g')
  .attr('class', 'axis axis--y')
  .style('opacity', 0)
  .call(bundle.axisLeft(y).ticks);

  gg.append('g')
  .selectAll('rect')
  .data(bundle.entries(freq['second_choice']))
  .enter().append('rect')
  .attr('id', 'second_choice-'+id)
  .attr('finalwidth', function(d) {
return x(d.value);
})
  .attr('x', x(0))
  .attr('y', function(d) {
return y(d.key);
})
  .attr('width', 0)
  .attr('height',
    firstFreqSvg.attr('height')/bundle.values(freq['second_choice']).length)
  .attr('fill', 'gray')
  .style('stroke', 'white')
  .style('opacity', 0.2);

  ggg.append('g')
  .selectAll('rect')
  .data(bundle.entries(freq['first_choice']))
  .enter().append('rect')
  .attr('id', 'first_choice-'+id)
  .attr('finalwidth', function(d) {
return x(d.value);
})
  .attr('finalx', function(d) {
return x(1-d.value);
})
  .attr('x', x(1))
  .attr('y', function(d) {
return y(d.key);
})
  .attr('width', 0)
  .attr('height',
    firstFreqSvg.attr('height')/bundle.values(freq['first_choice']).length)
  .attr('fill', 'gray')
  .style('stroke', 'white')
  .style('opacity', 0.2);

  gg.append('g')
  .selectAll('text')
  .data(bundle.entries(freq['second_choice']))
  .enter().append('text')
  .attr('x', x(0))
  .attr('dx', -2)
  .attr('y', function(d) {
return y(d.key);
})
  .attr('dy', y.bandwidth()/2+4)
  .style('font-size', '8pt')
  .style('text-anchor', 'end')
  .text(function(d) {
return parseInt(100*d.value)+'%';
});

  ggg.append('g')
  .selectAll('text')
  .data(bundle.entries(freq['first_choice']))
  .enter().append('text')
  .attr('x', x(1))
  .attr('dx', 2)
  .attr('y', function(d) {
return y(d.key);
})
  .attr('dy', y.bandwidth()/2+4)
  .style('font-size', '8pt')
  .style('text-anchor', 'start')
  .text(function(d) {
return parseInt(100*d.value)+'%';
});

  gg.append('g')
  .selectAll('text')
  .data(bundle.entries(freq['second_choice']))
  .enter().append('text')
  .attr('x', x(0))
  .attr('dx', 2)
  .attr('y', function(d) {
return y(d.key);
})
  .attr('dy', y.bandwidth()/2+4)
  .style('font-size', '8pt')
  .text(function(d) {
return d.key;
});

  return;
}


/** Search function
*  @param {String} className
*  @param {Object} searchBar
*  @function
*/
export function search(className, searchBar) {
  let items = document.querySelectorAll(className);
  for (let i=0; i<items.length; i++) {
    if (items[i].innerText.toLowerCase().indexOf(searchBar.value.toLowerCase())
      < 0) {
      items[i].style.display = 'none';
    } else {
      items[i].style.display = 'block';
    }
  }
  return;
}


/** Add dialog box to ids containing string dialog using #activate-id
*  @function
*/
export function addDialog() {
  [].forEach.call(document.querySelectorAll('[id^=dialog]'),
    (el) => {
      const dialog = bundle.dialog.MDCDialog.attachTo(el);
      document.querySelector('#activate-'+el.id).onclick = () => {
        dialog.show();
      };
    }
  );
}


/** Toggle image visibility
*  @function
*/
export function toggleImages() {
  console.info('Hi');
  [].forEach.call(document.querySelectorAll('.toggle-images'),
    (el) => {
      console.info(sessionStorage.images);
      const toggle = bundle.iconToggle.MDCIconToggle.attachTo(el);
      if (sessionStorage.images !== undefined) {
        if (sessionStorage.images == 'block') {
          toggle.on = true;
        } else {
          toggle.on = false;
        }
        [].forEach.call(document.querySelectorAll('.question-image'),
          (el) => {
            if (sessionStorage.images == 'block') {
              el.style.display = 'block';
            } else {
              el.style.display = 'none';
            }
          }
        );
      }
      el.addEventListener('MDCIconToggle:change', ({detail}) => {
        [].forEach.call(document.querySelectorAll('.question-image'),
          (el) => {
            if (detail.isOn) {
              el.style.display = 'block';
            } else {
              el.style.display = 'none';
            }
            sessionStorage.images = el.style.display;
          }
        );
      });
    }
  );
}

/** Toggle answer visibility
*  @function
*/
export function toggleAnswers() {
  [].forEach.call(document.querySelectorAll('.toggle-answers'),
    (el) => {
      const toggle = bundle.iconToggle.MDCIconToggle.attachTo(el);
      if (sessionStorage.answers) {
        if (sessionStorage.answers == 'block') {
          toggle.on = true;
        } else {
          toggle.on = false;
        }
        [].forEach.call(document.querySelectorAll('.question-answers'),
          (el) => {
            el.style.display = sessionStorage.answers;
          }
        );
      }
      el.addEventListener('MDCIconToggle:change', ({detail}) => {
        [].forEach.call(document.querySelectorAll('.question-answers'),
          (el) => {
            if (detail.isOn) {
              el.style.display = 'block';
            } else {
              el.style.display = 'none';
            }
            sessionStorage.answers = el.style.display;
          }
        );
      });
    }
  );
}
// Commands
underlines();

// Listeners
window.addEventListener('resize', underlines);

// MDC
autoInit();
