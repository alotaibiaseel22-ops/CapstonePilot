import { useMutation } from '@tanstack/react-query'
import { analyzeProposal } from '../api/projects'

function useAnalyzeProposal(projectId) {
  return useMutation({
    mutationFn: (file) => analyzeProposal(projectId, file),
  })
}

export { useAnalyzeProposal }
