function ErrorState({ message = "Wystąpił błąd." }) {
  return (
    <div className="state-box error-box">
      <p>{message}</p>
    </div>
  );
}

export default ErrorState;
