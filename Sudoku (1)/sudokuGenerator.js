export const generateSudoku = async (level) => {
    try {
        const response = await fetch(`http://127.0.0.1:5000/generate?level=${level}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        console.log(data.grid)
        return {
            solution: data.solution,
            grid: data.grid
        };
    } catch (error) {
        console.error("Failed to generate Sudoku from API:", error);
        return { solution: [], grid: [] };
    }
};
