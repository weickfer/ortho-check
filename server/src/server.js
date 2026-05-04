import express from 'express';
import cors from 'cors';
import multer from 'multer';
import { analyzeProgress } from './controllers/analyze-controller.js';

const app = express();
app.use(cors());
app.use(express.json());

const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

// Endpoint principal
app.post(
  '/api/analyze-progress', 
  upload.fields([
    { name: 'image-ref', maxCount: 1 }, 
    { name: 'image-current', maxCount: 1 }
  ]), 
  analyzeProgress
);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});
