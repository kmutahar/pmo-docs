const express = require('express');
const widgets = require('./routes/widgets');

const app = express();
app.use(express.json());
app.use('/widgets', widgets);
app.listen(3000);
