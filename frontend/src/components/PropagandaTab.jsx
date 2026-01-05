import React from "react";

const PropagandaTab = ({ propScore }) => {
	let score = propScore.propaganda_probability * 100;
	let propList = propScore.formatted_result;

	return (
		<div>
			<div className="flex flex-col items-center justify-center space-y-2 border-2 border-green-500 bg-green-100 rounded-lg p-8">
				<div className="text-3xl font-bold">{score.toFixed(2)}%</div>
				<div className="text-sm text-gray-600">Propaganda Probability</div>
			</div>
		</div>
	);
};

export default PropagandaTab;
