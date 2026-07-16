import { useMutation } from '@tanstack/react-query'
import { analyzeProposal } from '../api/projects'

function useAnalyzeProposal() {
  return useMutation({
    mutationFn: ({ projectId, file }) => analyzeProposal(projectId, file),
  })
}

export { useAnalyzeProposal }
