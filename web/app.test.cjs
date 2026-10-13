const test = require('node:test');
const assert = require('node:assert/strict');
const { assess } = require('./app.js');
const infant = {age_months: 12, gcs: 15, hours_since_injury: 2, exclusion_present: false,
  altered_mental_status: false, severe_mechanism: false, palpable_skull_fracture: false,
  nonfrontal_scalp_hematoma: false, loc_at_least_5_seconds: false, not_acting_normally: false};
const child = {age_months: 72, gcs: 15, hours_since_injury: 4, exclusion_present: false,
  altered_mental_status: false, severe_mechanism: false, basilar_skull_fracture_signs: false,
  any_loss_of_consciousness: false, vomiting: false, severe_headache: false};
for (const [name, base] of [['infant',infant],['older child',child]]) {
  test(name + ' very low', () => assert.equal(assess(base).risk_tier, 'very_low'));
  test(name + ' GCS 14 high', () => assert.equal(assess({...base,gcs:14}).risk_tier, 'high'));
  test(name + ' altered mental status high', () => assert.equal(assess({...base,altered_mental_status:true}).risk_tier, 'high'));
  test(name + ' severe mechanism intermediate', () => assert.equal(assess({...base,severe_mechanism:true}).risk_tier, 'intermediate'));
}
for (const factor of ['palpable_skull_fracture','nonfrontal_scalp_hematoma','loc_at_least_5_seconds','not_acting_normally']) {
  test('infant ' + factor, () => assert.equal(assess({...infant,[factor]:true}).risk_tier,
    factor==='palpable_skull_fracture' ? 'high' : 'intermediate'));
}
for (const factor of ['basilar_skull_fracture_signs','any_loss_of_consciousness','vomiting','severe_headache']) {
  test('older ' + factor, () => assert.equal(assess({...child,[factor]:true}).risk_tier,
    factor==='basilar_skull_fracture_signs' ? 'high' : 'intermediate'));
}
for (const invalid of [{gcs:13},{age_months:216},{hours_since_injury:25},{exclusion_present:true},{vomiting:null}]) {
  test('reject invalid older input ' + JSON.stringify(invalid), () => assert.throws(() => assess({...child,...invalid})));
}
test('age transition', () => {
  assert.equal(assess({...infant,age_months:23}).age_group,'under_2');
  assert.equal(assess({...child,age_months:24}).age_group,'2_and_older');
});
test('missing age and time are invalid', () => {
  assert.throws(() => assess({...child,age_months:''}));
  assert.throws(() => assess({...child,hours_since_injury:''}));
});
