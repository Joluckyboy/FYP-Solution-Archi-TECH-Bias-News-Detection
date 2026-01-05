import { PieChart, Pie, Tooltip, Cell, Legend } from "recharts";
import React from "react";
// Note: The numbers for emotion seems to not be adding up to 1, will add disclaimer for frontend

// "neutral": 0.43537326214104244,
// "approval": 0.2658073998602011,
// "optimism": 0.1969787107371157,
// "curiosity": 0.09566417400776189,
// "confusion": 0.06997088699574343,
// "realization": 0.039681326268158366,
// "caring": 0.030908850730806927,
// "disapproval": 0.021317740121195392,
// "disappointment": 0.018779978953967037,
// "desire": 0.018416335818127905,
// "admiration": 0.007938143007725544,
// "annoyance": 0.007238971263684461,
// "sadness": 0.005683775009574831,
// "joy": 0.005526566468018533,
// "relief": 0.005179896931159077,
// "nervousness": 0.004267771174294199,
// "excitement": 0.0032712773984788575,
// "amusement": 0.0031110157004624974,
// "fear": 0.0030632778704907,
// "remorse": 0.002037806592047472,
// "love": 0.0017748313359650719,
// "pride": 0.0015037857885199998,
// "gratitude": 0.0014730517472390616,
// "surprise": 0.0013903546844317737,
// "anger": 0.0009211189136613337,
// "grief": 0.0008032292307341236,
// "embarrassment": 0.0007378618384516517,
// "disgust": 0.0007374147870225046

// Define colors for the pie slices
// const COLORS = [
//   "#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#BAE1FF",
//   "#D4A5A5", "#D4C5A5", "#D4D4A5", "#A5D4A5", "#A5D4D4",
//   "#C9A5D4", "#D4A5C9", "#A5A5D4", "#A5C9D4", "#C9D4A5",
//   "#FFD1DC", "#FFB347", "#FF6961", "#77DD77", "#AEC6CF"
// ];
const COLORS = [
	"#8884d8",
	"#82ca9d",
	"#ffc658",
	"#ff8042",
	"#ff6361",
	"#a4de6c",
	"#d0ed57",
	"#8dd1e1",
	"#d884d8",
	"#84a9d8",
];

const RADIAN = Math.PI / 180;
// const renderCustomizedLabel = ({
// 	cx,
// 	cy,
// 	midAngle,
// 	innerRadius,
// 	outerRadius,
// 	value,
// 	index,
// }) => {
// 	if (value < 7) return null; // Only show label if value is more than 7%

// 	const radius = innerRadius + (outerRadius - innerRadius) * 0.55; // Adjust the radius to be closer to the edge
// 	const x = cx + radius * Math.cos(-midAngle * RADIAN);
// 	const y = cy + radius * Math.sin(-midAngle * RADIAN);


//   let fontSize=16;

//   // Setting < 10% to zero for now, the slice is too small to fit the text, need to find a fix for this
//   if (value < 10){
//     fontSize=0;
//   }

// 	return (
// 		<text
// 			x={x}
// 			y={y}
// 			fill="white"
// 			textAnchor={x > cx ? "start" : "end"}
// 			dominantBaseline="central"
// 		 style={{ fontSize: `${fontSize}px` }}>
// 			{`${value.toFixed(2)}%`}
// 		</text>
// 	);
// };
const renderCustomizedLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    value,
    index,
}) => {
    if (value < 7) return null; // Only show label if value is more than 7%

    const radius = innerRadius + (outerRadius - innerRadius) * 0.75; // Adjust the radius to be closer to the edge
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    let fontSize = 16;

    // Setting < 10% to zero for now, the slice is too small to fit the text, need to find a fix for this
    if (value < 10) {
        fontSize = 0;
    }

    return (
        <text
            x={x}
            y={y}
            fill="white"
            textAnchor="middle"
            dominantBaseline="central"
            style={{ fontSize: `${fontSize}px`, fontWeight: "bold" }}>
            {`${value.toFixed(2)}%`}
        </text>
    );
};

const renderLegend = (props) => {
	const { payload } = props;
	return (
		<ul>
			{payload.map((entry, index) => (
				<li key={`item-${index}`} style={{ color: entry.color }}>
					{`${entry.value}: ${entry.payload.value.toFixed(2)}%`}
				</li>
			))}
		</ul>
	);
};

// Main Pie Chart Component
const EmotionPieChart = ({ weightedAvg }) => {
	// console.log("EmotionPieChart weightedAvg:", weightedAvg);
	// Convert object to array of { name, value } format
	const chartData = Object.entries(weightedAvg).map(([key, value]) => ({
		name: key,
		value: value * 100,
	}));

    // console.log("EmotionPieChart chartData:", chartData);

      // Sort in descending order
      chartData.sort((a, b) => b.value - a.value);

      let top = chartData.slice(0, 5);

      // othersValue = Remaining percentage after top 4 emotions
      let othersValue = 0; 
      for (let i = 5; i < chartData.length; i++) {
        othersValue += chartData[i].value;
      }

      // Add "Others" as the 5th item
      top.push({ name: "Others", value: othersValue }); 
      let finalData = top; 
    
  return (
    <PieChart width={500} height={500}>
      <Pie
        data={finalData}
        dataKey="value"
        nameKey="name"
        cx="50%"
        cy="50%"
        outerRadius={150}
        fill="#8884d8"
        
        labelLine={false}
        label={renderCustomizedLabel}
        >
        {finalData.map((_, index) => (
          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
        ))}
      </Pie>
      <Tooltip />
      <Legend layout="vertical" align="right" verticalAlign="middle" content={renderLegend} />
    </PieChart>
  );
};

export default EmotionPieChart;
