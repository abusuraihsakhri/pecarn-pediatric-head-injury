/* PECARN Figure 3 (Kuppermann et al., Lancet 2009) decision-rule categories.
 * No personal data or network calls. Not an individual risk predictor. */
(function (root) {
  'use strict';
  const younger = ['palpable_skull_fracture', 'nonfrontal_scalp_hematoma', 'loc_at_least_5_seconds', 'not_acting_normally'];
  const older = ['basilar_skull_fracture_signs', 'any_loss_of_consciousness', 'vomiting', 'severe_headache'];
  const shared = ['altered_mental_status', 'severe_mechanism'];
  const guidance = {
    high: 'CT recommended by the PECARN algorithm; arrange urgent clinical assessment.',
    intermediate: 'Observation versus CT; use clinical judgment, evolution of findings, and shared decision-making.',
    very_low: 'CT generally not recommended by PECARN for an otherwise eligible child; provide clinical reassessment and precautions.'
  };

  function assess(data) {
    if (data.age_months === '' || data.age_months == null || data.hours_since_injury === '' || data.hours_since_injury == null) {
      throw new Error('Age and time since injury are required.');
    }
    const age = Number(data.age_months);
    const gcs = Number(data.gcs);
    const hours = Number(data.hours_since_injury);
    if (!Number.isInteger(age) || age < 0 || age >= 216) throw new Error('Age must be a whole number from 0 to 215 months.');
    if (!Number.isInteger(gcs) || ![14, 15].includes(gcs)) throw new Error('Rule applies only to GCS 14–15.');
    if (!Number.isFinite(hours) || hours < 0 || hours > 24) throw new Error('Presentation must be within 24 hours of injury.');
    if (data.exclusion_present !== false) throw new Error('An applicable study population and absence of exclusions must be confirmed.');
    const under2 = age < 24;
    const relevant = [...shared, ...(under2 ? younger : older)];
    const irrelevant = under2 ? older : younger;
    for (const name of irrelevant) {
      if (Object.hasOwn(data, name) && data[name] !== null && data[name] !== '') throw new Error(name + ' does not apply at this age.');
    }
    for (const name of relevant) {
      if (typeof data[name] !== 'boolean') throw new Error('Answer required for ' + name.replaceAll('_', ' ') + '.');
    }
    const high = gcs === 14 ? ['GCS 14'] : [];
    if (data.altered_mental_status) high.push('Altered mental status');
    const intermediate = [];
    if (under2) {
      if (data.palpable_skull_fracture) high.push('Palpable skull fracture');
      if (data.nonfrontal_scalp_hematoma) intermediate.push('Non-frontal scalp hematoma');
      if (data.loc_at_least_5_seconds) intermediate.push('Loss of consciousness ≥5 seconds');
      if (data.severe_mechanism) intermediate.push('Severe injury mechanism');
      if (data.not_acting_normally) intermediate.push('Not acting normally according to parent');
    } else {
      if (data.basilar_skull_fracture_signs) high.push('Signs of basilar skull fracture');
      if (data.any_loss_of_consciousness) intermediate.push('Any loss of consciousness');
      if (data.vomiting) intermediate.push('Vomiting');
      if (data.severe_mechanism) intermediate.push('Severe injury mechanism');
      if (data.severe_headache) intermediate.push('Severe headache');
    }
    const tier = high.length ? 'high' : intermediate.length ? 'intermediate' : 'very_low';
    return { age_group: under2 ? 'under_2' : '2_and_older', risk_tier: tier,
      predictors_present: [...high, ...intermediate], ct_guidance: guidance[tier] };
  }

  function initialize() {
    const form = document.querySelector('#pecarn-form');
    if (!form) return;
    const ageField = form.elements.namedItem('age_months');
    const youngSection = document.getElementById('under2-fields');
    const oldSection = document.getElementById('older-fields');
    const result = document.getElementById('result');
    const status = document.getElementById('status');
    const fields = [...shared, ...younger, ...older];
    function group() {
      const age = Number(ageField.value);
      const valid = ageField.value !== '' && Number.isInteger(age) && age >= 0 && age < 216;
      const under2 = valid && age < 24;
      youngSection.hidden = !under2;
      oldSection.hidden = !valid || under2;
      for (const name of younger) {
        const field = form.elements.namedItem(name);
        field.disabled = !under2;
        field.required = under2;
      }
      for (const name of older) {
        const field = form.elements.namedItem(name);
        field.disabled = !valid || under2;
        field.required = valid && !under2;
      }
      result.hidden = true;
      status.textContent = valid ? 'Age-specific rule: ' + (under2 ? 'under 2 years' : '2 through 17 years') : 'Enter an age to select criteria';
    }
    ageField.addEventListener('input', group);
    group();
    form.addEventListener('reset', () => {
      queueMicrotask(group);
      result.hidden = true;
    });
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      result.hidden = false;
      const heading = document.getElementById('result-heading');
      const message = document.getElementById('result-message');
      const predictors = document.getElementById('result-predictors');
      heading.textContent = 'Cannot assess';
      message.textContent = '';
      predictors.textContent = '';
      result.dataset.tier = 'error';
      try {
        const data = {
          age_months: ageField.value,
          gcs: form.elements.namedItem('gcs').value,
          hours_since_injury: form.elements.namedItem('hours_since_injury').value,
          exclusion_present: form.elements.namedItem('exclusion_present').value === 'yes'
        };
        if (form.elements.namedItem('exclusion_present').value === '') throw new Error('Confirm the study eligibility criteria first.');
        for (const name of fields) {
          const field = form.elements.namedItem(name);
          if (field.disabled) continue;
          if (field.value === '') throw new Error('Answer required: ' + name.replaceAll('_', ' ') + '.');
          data[name] = field.value === 'yes';
        }
        const output = assess(data);
        const labels = { high: 'High-risk branch', intermediate: 'Intermediate-risk branch', very_low: 'Very-low-risk branch' };
        heading.textContent = labels[output.risk_tier];
        message.textContent = output.ct_guidance;
        predictors.textContent = output.predictors_present.length ? 'Findings: ' + output.predictors_present.join('; ') : 'No PECARN prediction-tree factors identified.';
        result.dataset.tier = output.risk_tier;
      } catch (error) {
        message.textContent = error.message;
      }
      result.focus();
    });
  }
  const api = { assess };
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', initialize);
    root.PECARN = api;
  }
})(typeof window !== 'undefined' ? window : globalThis);
