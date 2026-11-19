/* Example data global for region_example_overview.js. Every name and value here is
 * fictional; replace them with descriptors copied from each provider's page and list the
 * page per row in PROVENANCE.md. Units go in the column label. Rows are sorted by group. */
window.DATASETS = {
  groups: {
    repoA: { label: 'Repository A', color: '#007AFF' },
    repoB: { label: 'Repository B', color: '#34C759' },
    vendC: { label: 'Vendor C',     color: '#FF9500' },
  },
  columns: [
    { key: 'labeled',  label: 'labels',            fmt: 'bool' },
    { key: 'rows',     label: 'rows (K)',          fmt: 'int' },
    { key: 'features', label: 'features',          fmt: 'k' },
    { key: 'classes',  label: 'classes',           fmt: 'int' },
    { key: 'missing',  label: 'missing (%)',       fmt: 'd1' },
    { key: 'size',     label: 'size (MB)',         fmt: 'int' },
  ],
  rows: [
    { label: 'Retail churn',    group: 'repoA', labeled: true,  rows: 41,  features: 23,   classes: 2,  missing: 0.4,  size: 12 },
    { label: 'Sensor drift',    group: 'repoA', labeled: true,  rows: 128, features: 512,  classes: 6,  missing: 3.1,  size: 260 },
    { label: 'Hospital stays',  group: 'repoA', labeled: false, rows: 77,  features: 61,   classes: 3,  missing: 11.8, size: 48 },
    { label: 'Crop parcels',    group: 'repoB', labeled: true,  rows: 302, features: 1840, classes: 14, missing: 0.0,  size: 910 },
    { label: 'Song tags',       group: 'repoB', labeled: true,  rows: 19,  features: 96,   classes: 9,  missing: 1.2,  size: 7 },
    { label: 'Fraud alerts',    group: 'vendC', labeled: false, rows: 655, features: 38,   classes: 2,  missing: 6.5,  size: 380 },
  ],
};
