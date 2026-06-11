function LoadingState({ message = "Ładowanie danych..." }) {
  return (
    <div className="state-box">
      <p>{message}</p>
    </div>
  );
}

export default LoadingState;
